import type { BaakEnv } from "./http";

export type FirestoreValue = {
  nullValue?: null;
  booleanValue?: boolean;
  integerValue?: string;
  doubleValue?: number;
  stringValue?: string;
  timestampValue?: string;
  referenceValue?: string;
  arrayValue?: { values?: FirestoreValue[] };
  mapValue?: { fields?: Record<string, FirestoreValue> };
};

export type FirestoreDocument = {
  name?: string;
  fields?: Record<string, FirestoreValue>;
  createTime?: string;
  updateTime?: string;
};

type FirestoreListResponse = {
  documents?: FirestoreDocument[];
  nextPageToken?: string;
};

type StructuredQuery = {
  from?: Array<{ collectionId: string; allDescendants?: boolean }>;
  where?: {
    fieldFilter?: {
      field: { fieldPath: string };
      op: "EQUAL" | "LESS_THAN" | "LESS_THAN_OR_EQUAL" | "GREATER_THAN" | "GREATER_THAN_OR_EQUAL" | "ARRAY_CONTAINS";
      value: FirestoreValue;
    };
    compositeFilter?: {
      op: "AND" | "OR";
      filters: Array<{ fieldFilter: NonNullable<StructuredQuery["where"]>["fieldFilter"] }>;
    };
  };
  orderBy?: Array<{ field: { fieldPath: string }; direction: "ASCENDING" | "DESCENDING" }>;
  limit?: number;
};

export function firestoreValue(value: unknown): FirestoreValue {
  if (value === null || value === undefined) return { nullValue: null };
  if (typeof value === "boolean") return { booleanValue: value };
  if (typeof value === "number") {
    return Number.isInteger(value) ? { integerValue: String(value) } : { doubleValue: value };
  }
  if (typeof value === "string") return { stringValue: value };
  if (Array.isArray(value)) return { arrayValue: { values: value.map(firestoreValue) } };
  if (typeof value === "object") {
    const fields: Record<string, FirestoreValue> = {};
    for (const [key, item] of Object.entries(value)) fields[key] = firestoreValue(item);
    return { mapValue: { fields } };
  }
  return { stringValue: String(value) };
}

export function decodeFirestoreValue(value: FirestoreValue | undefined): unknown {
  if (!value) return null;
  if ("nullValue" in value) return null;
  if ("booleanValue" in value) return value.booleanValue;
  if ("integerValue" in value) return Number(value.integerValue);
  if ("doubleValue" in value) return value.doubleValue;
  if ("stringValue" in value) return value.stringValue;
  if ("timestampValue" in value) return value.timestampValue;
  if ("referenceValue" in value) return value.referenceValue;
  if ("arrayValue" in value) return (value.arrayValue?.values || []).map(decodeFirestoreValue);
  if ("mapValue" in value) {
    const result: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value.mapValue?.fields || {})) result[key] = decodeFirestoreValue(item);
    return result;
  }
  return null;
}

export function decodeDocument(document: FirestoreDocument): Record<string, unknown> & { id: string } {
  const name = document.name || "";
  const id = name.split("/").pop() || "";
  const result: Record<string, unknown> & { id: string } = { id };
  for (const [key, value] of Object.entries(document.fields || {})) result[key] = decodeFirestoreValue(value);
  return result;
}

function projectId(env: BaakEnv): string {
  const value = env.FIREBASE_PROJECT_ID?.trim();
  if (!value) throw new Error("FIREBASE_PROJECT_ID is not configured");
  return value;
}

function firestoreBase(env: BaakEnv): string {
  const emulator = env.FIRESTORE_EMULATOR_HOST?.trim();
  if (emulator) return `http://${emulator}/v1/projects/${projectId(env)}/databases/(default)/documents`;
  return `https://firestore.googleapis.com/v1/projects/${projectId(env)}/databases/(default)/documents`;
}

function firestoreHeaders(env: BaakEnv): HeadersInit {
  const token = env.GOOGLE_OAUTH_ACCESS_TOKEN?.trim();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function firestoreFetch(env: BaakEnv, path: string, init: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const headers = new Headers(firestoreHeaders(env));
    headers.set("content-type", "application/json");
    for (const [key, value] of Object.entries(init.headers || {})) headers.set(key, String(value));
    return await fetch(`${firestoreBase(env)}${path}`, { ...init, headers, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

export async function listDocuments(
  collectionId: string,
  env: BaakEnv,
  options: { limit?: number; filters?: Array<{ fieldPath: string; value: unknown }> } = {},
): Promise<Array<Record<string, unknown> & { id: string }>> {
  const limit = Math.max(1, Math.min(100, options.limit ?? 100));
  const filters = (options.filters || []).map((filter) => ({
    fieldFilter: {
      field: { fieldPath: filter.fieldPath },
      op: "EQUAL" as const,
      value: firestoreValue(filter.value),
    },
  }));
  const where = filters.length === 1
    ? filters[0]
    : filters.length > 1
      ? { compositeFilter: { op: "AND" as const, filters } }
      : undefined;
  const query: StructuredQuery = {
    from: [{ collectionId }],
    where,
    orderBy: [{ field: { fieldPath: "title" }, direction: "ASCENDING" }],
    limit,
  };
  const response = await firestoreFetch(env, ":runQuery", {
    method: "POST",
    body: JSON.stringify({ structuredQuery: query }),
  });
  if (!response.ok) throw new Error(`Firestore query failed with status ${response.status}`);
  const values: unknown = await response.json();
  if (!Array.isArray(values)) return [];
  return values
    .filter((item): item is { document: FirestoreDocument } => Boolean(item && typeof item === "object" && "document" in item))
    .map((item) => decodeDocument(item.document));
}

export async function getDocument(
  collectionId: string,
  documentId: string,
  env: BaakEnv,
): Promise<(Record<string, unknown> & { id: string }) | null> {
  const response = await firestoreFetch(env, `/${encodeURIComponent(collectionId)}/${encodeURIComponent(documentId)}`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Firestore document read failed with status ${response.status}`);
  return decodeDocument(await response.json() as FirestoreDocument);
}

export async function listTopLevelDocuments(
  collectionId: string,
  env: BaakEnv,
  limit = 100,
  filters: Array<{ fieldPath: string; value: unknown }> = [],
): Promise<Array<Record<string, unknown> & { id: string }>> {
  const boundedLimit = Math.max(1, Math.min(100, limit));
  if (filters.length === 0) {
    const response = await firestoreFetch(env, `/${encodeURIComponent(collectionId)}?pageSize=${boundedLimit}`);
    if (!response.ok) throw new Error(`Firestore collection read failed with status ${response.status}`);
    const payload = await response.json() as FirestoreListResponse;
    return (payload.documents || []).map(decodeDocument);
  }

  const fieldFilters = filters.map((filter) => ({
    fieldFilter: {
      field: { fieldPath: filter.fieldPath },
      op: "EQUAL" as const,
      value: firestoreValue(filter.value),
    },
  }));
  const where = fieldFilters.length === 1
    ? fieldFilters[0]
    : { compositeFilter: { op: "AND" as const, filters: fieldFilters } };
  const query: StructuredQuery = {
    from: [{ collectionId }],
    where,
    limit: boundedLimit,
  };
  const response = await firestoreFetch(env, ":runQuery", {
    method: "POST",
    body: JSON.stringify({ structuredQuery: query }),
  });
  if (!response.ok) throw new Error(`Firestore filtered collection read failed with status ${response.status}`);
  const values: unknown = await response.json();
  if (!Array.isArray(values)) return [];
  return values
    .filter((item): item is { document: FirestoreDocument } => Boolean(item && typeof item === "object" && "document" in item))
    .map((item) => decodeDocument(item.document));
}
