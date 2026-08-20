import type { PagesFunction } from "@cloudflare/workers-types";

export type BaakEnv = {
  FIREBASE_PROJECT_ID?: string;
  FIRESTORE_EMULATOR_HOST?: string;
  GOOGLE_OAUTH_ACCESS_TOKEN?: string;
  GOOGLE_SERVICE_ACCOUNT_EMAIL?: string;
  GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY?: string;
  TRUSTED_ORDER_FUNCTION_URL?: string;
  TRUSTED_ADMIN_FUNCTION_URL?: string;
  ALLOWED_ORIGIN?: string;
  LOCAL_FLASK_API?: string;
};

export type BaakContext = Parameters<PagesFunction<BaakEnv>>[0];

export function getRequestId(request: Request): string {
  const supplied = request.headers.get("x-request-id")?.trim();
  return supplied && supplied.length <= 128 ? supplied : `req_${crypto.randomUUID()}`;
}

function corsHeaders(request: Request, env: BaakEnv): Headers {
  const headers = new Headers({
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  const requestOrigin = request.headers.get("Origin");
  const configuredOrigin = env.ALLOWED_ORIGIN || requestOrigin || "*";
  const origin = configuredOrigin === "*" || configuredOrigin === requestOrigin ? configuredOrigin : "null";
  headers.set("Access-Control-Allow-Origin", origin);
  headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization, Idempotency-Key, X-Request-ID, X-Turnstile-Token");
  headers.set("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");
  headers.set("Vary", "Origin");
  return headers;
}

export function jsonResponse(
  payload: unknown,
  request: Request,
  env: BaakEnv,
  status = 200,
  extraHeaders: Record<string, string> = {},
): Response {
  const headers = corsHeaders(request, env);
  for (const [key, value] of Object.entries(extraHeaders)) headers.set(key, value);
  return new Response(JSON.stringify(payload), { status, headers });
}

export function errorResponse(
  code: string,
  message: string,
  request: Request,
  env: BaakEnv,
  status: number,
  details: Record<string, unknown> = {},
): Response {
  return jsonResponse(
    { ok: false, error: { code, message, requestId: getRequestId(request), ...details } },
    request,
    env,
    status,
  );
}

export function methodNotAllowed(request: Request, env: BaakEnv, allowed: string[]): Response {
  return errorResponse("METHOD_NOT_ALLOWED", "طريقة الطلب غير مدعومة.", request, env, 405, { allowed });
}

export function handleOptions(request: Request, env: BaakEnv): Response {
  return new Response(null, { status: 204, headers: corsHeaders(request, env) });
}

export async function readJson(request: Request): Promise<Record<string, unknown>> {
  try {
    const value: unknown = await request.json();
    return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
  } catch {
    return {};
  }
}

export function bearerToken(request: Request): string | null {
  const value = request.headers.get("Authorization") || "";
  return value.startsWith("Bearer ") ? value.slice(7).trim() || null : null;
}
