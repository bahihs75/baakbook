/**
 * ADR: TrustedAdminFunction
 * =========================
 * Problem:
 *   Cloudflare Pages Functions must not receive server credentials or perform
 *   privileged Firestore writes directly. The existing admin page needs a
 *   trusted HTTP backend for authentication, authorization, and CRUD operations.
 *
 * Alternatives considered:
 *   1. Let the browser write Firestore directly — rejected because the browser
 *      is untrusted and the admin surface would be broader than necessary.
 *   2. Put a service-account credential in Cloudflare Pages — rejected because
 *      it would create a high-impact secret in the edge runtime.
 *   3. Use a Firebase HTTPS Function with Admin SDK — chosen because it can
 *      verify Firebase ID tokens, enforce the admin custom claim, and perform
 *      atomic Firestore writes without exposing credentials.
 *
 * Decision:
 *   Expose one regional HTTPS function and route only the documented admin
 *   resources through it. Every request verifies a Firebase ID token and the
 *   `admin: true` custom claim before touching Firestore.
 *
 * Consequences:
 *   + Privileged operations remain server-authoritative.
 *   + The Pages layer can stay credential-free and act as a same-origin proxy.
 *   - The function must be deployed and the admin claim must be assigned to the
 *     intended Firebase account before the dashboard can be used.
 */

import { getApp, getApps, initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";
import { FieldValue, getFirestore, type DocumentData, type DocumentSnapshot } from "firebase-admin/firestore";
import { onRequest } from "firebase-functions/v2/https";
import { logger } from "firebase-functions";
import type { Request, Response } from "express";

const REGION = "europe-west1";
const firebaseApp = getApps().length > 0 ? getApp() : initializeApp();
const db = getFirestore(firebaseApp);
const auth = getAuth(firebaseApp);

const ALLOWED_ORDER_STATUSES = new Set([
  "new",
  "confirmed",
  "awaiting_supply",
  "processing",
  "ready_to_ship",
  "shipped",
  "delivered",
  "cancelled",
  "returned",
]);

const MAX_LIST_SIZE = 500;

type JsonObject = Record<string, unknown>;

type AdminRequest = {
  method: string;
  path: string;
  requestId: string;
  body: JsonObject;
  uid: string;
};

function asString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function asFiniteNumber(value: unknown): number | null {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function asInteger(value: unknown): number | null {
  const parsed = asFiniteNumber(value);
  return parsed !== null && Number.isInteger(parsed) ? parsed : null;
}

function objectValue(value: unknown): JsonObject {
  return value && typeof value === "object" && !Array.isArray(value) ? value as JsonObject : {};
}

function jsonError(res: Response, status: number, code: string, message: string, requestId: string): void {
  res.status(status).json({ error: message, code, requestId });
}

function jsonOk(res: Response, payload: unknown, status = 200): void {
  res.status(status).json(payload);
}

function requestPath(req: Request): string {
  return String(req.path || req.url || "").replace(/^\/+|\/+$/g, "");
}

function requestId(req: Request): string {
  const supplied = asString(req.get("x-request-id"));
  return supplied || `admin_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function parseBody(req: Request): JsonObject {
  if (!req.body) return {};
  if (typeof req.body === "object" && !Buffer.isBuffer(req.body)) return objectValue(req.body);
  if (typeof req.body === "string") {
    try {
      return objectValue(JSON.parse(req.body));
    } catch {
      return {};
    }
  }
  return {};
}

function timestampValue(value: unknown): string {
  if (!value) return new Date(0).toISOString();
  if (value instanceof Date) return value.toISOString();
  if (typeof value === "object" && value !== null && "toDate" in value && typeof (value as { toDate?: unknown }).toDate === "function") {
    return ((value as { toDate: () => Date }).toDate()).toISOString();
  }
  if (typeof value === "string" || typeof value === "number") {
    const date = new Date(value);
    if (!Number.isNaN(date.getTime())) return date.toISOString();
  }
  return new Date(0).toISOString();
}

function productPayload(id: string, raw: DocumentData): JsonObject {
  return {
    ...raw,
    id,
    active: raw.active !== false,
    archived: raw.archived === true,
    availability_type: raw.availability_type === "on_demand" ? "on_demand" : "in_stock",
    stock_quantity: asInteger(raw.stock_quantity) ?? 0,
    price: asInteger(raw.price) ?? 0,
    lead_time_min_days: Math.max(0, Math.min(1, asInteger(raw.lead_time_min_days ?? raw.lead_time_days) ?? 0)),
    lead_time_max_days: Math.max(0, Math.min(1, asInteger(raw.lead_time_max_days ?? raw.lead_time_days) ?? 0)),
  };
}

function orderPayload(id: string, raw: DocumentData): JsonObject {
  const customer = objectValue(raw.customer);
  const delivery = objectValue(raw.delivery);
  const items = Array.isArray(raw.items) ? raw.items : [];
  const gift = raw.gift && typeof raw.gift === "object" ? raw.gift : null;
  const timestamp = raw.createdAt ?? raw.timestamp ?? raw.created_at;
  const deliveryFee = raw.deliveryFee ?? raw.delivery_fee ?? 0;
  const wilaya = delivery.wilaya ?? raw.wilaya ?? raw.wilaya_num ?? "";
  const deliveryType = delivery.delivery_type ?? raw.delivery_type ?? "stop_desk";

  return {
    ...raw,
    order_id: asString(raw.order_id) || asString(raw.id) || id,
    id,
    timestamp: timestampValue(timestamp),
    customer_name: asString(customer.name ?? raw.customer_name),
    phone: asString(customer.phone ?? raw.phone),
    wilaya,
    delivery_type: deliveryType,
    address: asString(customer.address ?? raw.address),
    order_type: gift ? "gift" : items.some((item) => objectValue(item).availability_type === "on_demand") ? "on_demand" : "regular",
    items,
    gift,
    subtotal: asFiniteNumber(raw.subtotal) ?? 0,
    delivery_fee: asFiniteNumber(deliveryFee) ?? 0,
    total: asFiniteNumber(raw.total) ?? 0,
    status: asString(raw.status) || "new",
  };
}

async function verifyAdmin(req: Request): Promise<string> {
  const header = asString(req.get("authorization"));
  if (!header.startsWith("Bearer ")) {
    const error = new Error("AUTH_REQUIRED");
    error.name = "AUTH_REQUIRED";
    throw error;
  }
  const token = header.slice("Bearer ".length).trim();
  if (!token) {
    const error = new Error("AUTH_REQUIRED");
    error.name = "AUTH_REQUIRED";
    throw error;
  }
  const decoded = await auth.verifyIdToken(token, true);
  if (decoded.admin !== true && decoded.role !== "admin") {
    const error = new Error("ADMIN_REQUIRED");
    error.name = "ADMIN_REQUIRED";
    throw error;
  }
  return decoded.uid;
}

async function listDocuments(collection: string): Promise<Array<{ id: string; data: DocumentData }>> {
  const snapshot = await db.collection(collection).limit(MAX_LIST_SIZE).get();
  return snapshot.docs.map((doc) => ({ id: doc.id, data: doc.data() }));
}

async function handleProducts(req: AdminRequest, res: Response): Promise<void> {
  const segments = req.path.split("/").filter(Boolean);
  const id = segments[1] ? decodeURIComponent(segments[1]) : "";

  if (req.method === "GET") {
    const docs = await listDocuments("products");
    docs.sort((a, b) => asString(a.data.title).localeCompare(asString(b.data.title), "ar"));
    return jsonOk(res, docs.map(({ id: documentId, data }) => productPayload(documentId, data)));
  }

  if (req.method === "POST" && !id) {
    const productId = asString(req.body.id);
    const title = asString(req.body.title);
    const price = asInteger(req.body.price);
    if (!productId || !title || price === null || price <= 0) return jsonError(res, 400, "PRODUCT_INVALID", "معرّف الكتاب والعنوان والسعر مطلوبة.", req.requestId);
    const ref = db.collection("products").doc(productId);
    if ((await ref.get()).exists) return jsonError(res, 409, "PRODUCT_EXISTS", "معرّف الكتاب مستخدم من قبل.", req.requestId);
    const now = FieldValue.serverTimestamp();
    const data = { ...req.body, id: productId, price, title, createdAt: now, updatedAt: now, schemaVersion: 1 };
    await ref.create(data);
    return jsonOk(res, productPayload(productId, data), 201);
  }

  if (!id) return jsonError(res, 405, "METHOD_NOT_ALLOWED", "العملية غير مدعومة لهذا المسار.", req.requestId);
  const ref = db.collection("products").doc(id);
  const existing = await ref.get();
  if (!existing.exists) return jsonError(res, 404, "PRODUCT_NOT_FOUND", "الكتاب غير موجود.", req.requestId);

  if (req.method === "PUT" || req.method === "PATCH") {
    const price = req.body.price === undefined ? undefined : asInteger(req.body.price);
    const stock = req.body.stock_quantity === undefined ? undefined : asInteger(req.body.stock_quantity);
    if (price !== undefined && (price === null || price <= 0)) return jsonError(res, 400, "PRODUCT_INVALID", "السعر يجب أن يكون عددًا صحيحًا موجبًا.", req.requestId);
    if (stock !== undefined && (stock === null || stock < 0)) return jsonError(res, 400, "PRODUCT_INVALID", "المخزون يجب ألا يكون سالبًا.", req.requestId);
    const update: DocumentData = { ...req.body, updatedAt: FieldValue.serverTimestamp() };
    delete update.id;
    if (price !== undefined) update.price = price;
    if (stock !== undefined) update.stock_quantity = stock;
    if (update.availability_type === "on_demand") {
      update.lead_time_min_days = Math.max(0, Math.min(1, asInteger(update.lead_time_min_days ?? update.lead_time_days) ?? 0));
      update.lead_time_max_days = Math.max(update.lead_time_min_days, Math.min(1, asInteger(update.lead_time_max_days ?? update.lead_time_days) ?? 0));
    }
    await ref.set(update, { merge: true });
    return jsonOk(res, productPayload(id, { ...existing.data(), ...update }));
  }

  if (req.method === "DELETE") {
    await ref.delete();
    return jsonOk(res, { ok: true, id });
  }

  return jsonError(res, 405, "METHOD_NOT_ALLOWED", "الطريقة غير مدعومة.", req.requestId);
}

async function handleCategories(req: AdminRequest, res: Response): Promise<void> {
  const segments = req.path.split("/").filter(Boolean);
  const encodedName = segments[1] || "";
  const name = encodedName ? decodeURIComponent(encodedName) : "";
  const collection = db.collection("categories");

  if (req.method === "GET") {
    const docs = await listDocuments("categories");
    const names = docs
      .filter(({ data }) => data.active !== false)
      .map(({ id, data }) => asString(data.name) || id)
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b, "ar"));
    return jsonOk(res, names);
  }

  if (req.method === "POST" && !name) {
    const newName = asString(req.body.name);
    if (!newName) return jsonError(res, 400, "CATEGORY_INVALID", "اسم التصنيف مطلوب.", req.requestId);
    const ref = collection.doc(newName);
    if ((await ref.get()).exists) return jsonError(res, 409, "CATEGORY_EXISTS", "التصنيف موجود من قبل.", req.requestId);
    await ref.create({ name: newName, active: true, createdAt: FieldValue.serverTimestamp(), updatedAt: FieldValue.serverTimestamp() });
    return jsonOk(res, { name: newName }, 201);
  }

  if (!name) return jsonError(res, 405, "METHOD_NOT_ALLOWED", "العملية غير مدعومة لهذا المسار.", req.requestId);
  const oldRef = collection.doc(name);
  let oldSnapshot: DocumentSnapshot = await oldRef.get();
  if (!oldSnapshot.exists) {
    const query = await collection.where("name", "==", name).limit(1).get();
    if (query.empty) return jsonError(res, 404, "CATEGORY_NOT_FOUND", "التصنيف غير موجود.", req.requestId);
    oldSnapshot = query.docs[0];
  }

  if (req.method === "PUT" || req.method === "PATCH") {
    const newName = asString(req.body.name);
    if (!newName) return jsonError(res, 400, "CATEGORY_INVALID", "اسم التصنيف مطلوب.", req.requestId);
    if (newName === name) {
      await oldSnapshot.ref.set({ name: newName, updatedAt: FieldValue.serverTimestamp() }, { merge: true });
      return jsonOk(res, { name: newName });
    }
    const newRef = collection.doc(newName);
    if ((await newRef.get()).exists) return jsonError(res, 409, "CATEGORY_EXISTS", "التصنيف الجديد موجود من قبل.", req.requestId);
    const products = await collection.firestore.collection("products").where("category", "==", name).get();
    const batch = collection.firestore.batch();
    batch.set(newRef, { ...(oldSnapshot.data() || {}), name: newName, active: true, updatedAt: FieldValue.serverTimestamp() });
    products.docs.forEach((product) => batch.update(product.ref, { category: newName, updatedAt: FieldValue.serverTimestamp() }));
    batch.delete(oldSnapshot.ref);
    await batch.commit();
    return jsonOk(res, { name: newName });
  }

  if (req.method === "DELETE") {
    const products = await collection.firestore.collection("products").where("category", "==", name).limit(1).get();
    if (!products.empty) return jsonError(res, 409, "CATEGORY_IN_USE", "لا يمكن حذف تصنيف مرتبط بكتب.", req.requestId);
    await oldSnapshot.ref.delete();
    return jsonOk(res, { ok: true, name });
  }

  return jsonError(res, 405, "METHOD_NOT_ALLOWED", "الطريقة غير مدعومة.", req.requestId);
}

async function handleOrders(req: AdminRequest, res: Response): Promise<void> {
  const segments = req.path.split("/").filter(Boolean);
  const id = segments[1] ? decodeURIComponent(segments[1]) : "";
  const collection = db.collection("orders");

  if (req.method === "GET" && !id) {
    const docs = await listDocuments("orders");
    docs.sort((a, b) => timestampValue(b.data.createdAt ?? b.data.timestamp).localeCompare(timestampValue(a.data.createdAt ?? a.data.timestamp)));
    return jsonOk(res, docs.map(({ id: documentId, data }) => orderPayload(documentId, data)));
  }

  if (!id) return jsonError(res, 405, "METHOD_NOT_ALLOWED", "العملية غير مدعومة لهذا المسار.", req.requestId);
  const ref = collection.doc(id);
  const snapshot = await ref.get();
  if (!snapshot.exists) return jsonError(res, 404, "ORDER_NOT_FOUND", "الطلب غير موجود.", req.requestId);

  if (req.method === "PUT" || req.method === "PATCH") {
    const status = asString(req.body.status);
    if (!ALLOWED_ORDER_STATUSES.has(status)) return jsonError(res, 400, "ORDER_STATUS_INVALID", "حالة الطلب غير صالحة.", req.requestId);
    await ref.set({ status, updatedAt: FieldValue.serverTimestamp() }, { merge: true });
    return jsonOk(res, orderPayload(id, { ...snapshot.data(), status }));
  }

  if (req.method === "DELETE") {
    await ref.delete();
    return jsonOk(res, { ok: true, id });
  }

  return jsonError(res, 405, "METHOD_NOT_ALLOWED", "الطريقة غير مدعومة.", req.requestId);
}

async function handleSettings(req: AdminRequest, res: Response): Promise<void> {
  const ref = db.doc("settings/public");
  if (req.method === "GET") {
    const snapshot = await ref.get();
    return jsonOk(res, { ...(snapshot.data() || {}), features: objectValue(snapshot.data()?.features) });
  }
  if (req.method === "PUT" || req.method === "PATCH") {
    const features = objectValue(req.body.features);
    const allowed = ["discovery", "gifts", "gift_from_product", "gift_from_cart", "gift_finder", "on_demand", "ideas_lab", "dark_mode", "community", "smart_search"];
    const normalized = Object.fromEntries(allowed.map((key) => [key, features[key] === true]));
    await ref.set({ features: normalized, updatedAt: FieldValue.serverTimestamp() }, { merge: true });
    return jsonOk(res, { features: normalized });
  }
  return jsonError(res, 405, "METHOD_NOT_ALLOWED", "الطريقة غير مدعومة.", req.requestId);
}

async function findDeliveryFee(num: number): Promise<DocumentSnapshot | null> {
  const byId = await db.collection("deliveryFees").doc(String(num)).get();
  if (byId.exists) return byId;
  const query = await db.collection("deliveryFees").where("num", "==", num).limit(1).get();
  return query.empty ? null : query.docs[0];
}

async function handleDeliveryFees(req: AdminRequest, res: Response): Promise<void> {
  const segments = req.path.split("/").filter(Boolean);
  const numText = segments[1] || "";
  const num = numText ? asInteger(decodeURIComponent(numText)) : null;

  if (req.method === "GET" && num === null) {
    const docs = await listDocuments("deliveryFees");
    docs.sort((a, b) => (asInteger(a.data.num) ?? 0) - (asInteger(b.data.num) ?? 0));
    return jsonOk(res, docs.map(({ id, data }) => ({ ...data, id, num: asInteger(data.num) ?? Number(id) })));
  }
  if (num === null) return jsonError(res, 400, "DELIVERY_FEE_INVALID", "رقم الولاية غير صالح.", req.requestId);
  if (req.method !== "PUT" && req.method !== "PATCH") return jsonError(res, 405, "METHOD_NOT_ALLOWED", "الطريقة غير مدعومة.", req.requestId);

  const snapshot = await findDeliveryFee(num);
  if (!snapshot) return jsonError(res, 404, "DELIVERY_FEE_NOT_FOUND", "رسوم الولاية غير موجودة.", req.requestId);
  const stopDesk = asInteger(req.body.stop_desk);
  const domicile = asInteger(req.body.domicile);
  if (stopDesk === null || domicile === null || stopDesk < -1 || domicile < -1) return jsonError(res, 400, "DELIVERY_FEE_INVALID", "رسوم التوصيل يجب أن تكون أعدادًا صحيحة.", req.requestId);
  await snapshot.ref.set({ stop_desk: stopDesk, domicile, updatedAt: FieldValue.serverTimestamp() }, { merge: true });
  return jsonOk(res, { ...(snapshot.data() || {}), id: snapshot.id, num, stop_desk: stopDesk, domicile });
}

async function dispatch(adminRequest: AdminRequest, res: Response): Promise<void> {
  const resource = adminRequest.path.split("/")[0];
  switch (resource) {
    case "products": return handleProducts(adminRequest, res);
    case "categories": return handleCategories(adminRequest, res);
    case "orders": return handleOrders(adminRequest, res);
    case "settings": return handleSettings(adminRequest, res);
    case "delivery-fees": return handleDeliveryFees(adminRequest, res);
    default: return jsonError(res, 404, "ADMIN_ROUTE_NOT_FOUND", "مسار الإدارة غير موجود.", adminRequest.requestId);
  }
}

export const adminTrusted = onRequest(
  { region: REGION, timeoutSeconds: 30, memory: "256MiB" },
  async (req, res) => {
    const id = requestId(req);
    res.set("Cache-Control", "no-store");
    res.set("X-Request-ID", id);
    if (req.method === "OPTIONS") {
      res.status(204).end();
      return;
    }

    try {
      const uid = await verifyAdmin(req);
      const adminRequest: AdminRequest = {
        method: req.method,
        path: requestPath(req),
        requestId: id,
        body: parseBody(req),
        uid,
      };
      await dispatch(adminRequest, res);
    } catch (error) {
      const code = error instanceof Error ? error.name : "INTERNAL_ERROR";
      if (code === "AUTH_REQUIRED") {
        jsonError(res, 401, code, "يلزم تسجيل الدخول لإدارة المتجر.", id);
        return;
      }
      if (code === "ADMIN_REQUIRED") {
        jsonError(res, 403, code, "هذا الحساب لا يملك صلاحية إدارة المتجر.", id);
        return;
      }
      logger.error("admin_request_failed", { requestId: id, error: error instanceof Error ? error.message : String(error) });
      jsonError(res, 500, "ADMIN_INTERNAL_ERROR", "تعذر تنفيذ العملية الإدارية حاليًا.", id);
    }
  },
);
