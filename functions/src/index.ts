/**
 * ADR: TrustedOrderCreation
 * ==========================
 * Problem:
 *   The browser can alter prices, stock, gift eligibility, or delivery values.
 * Alternatives:
 *   1. Trust browser-submitted totals — rejected because the client is untrusted.
 *   2. Keep Flask as the order authority — rejected for the Pages migration.
 *   3. Use a Firebase callable Function with a Firestore transaction — chosen.
 * Decision:
 *   Re-read authoritative catalog and delivery documents, calculate totals on the
 *   server, and create an order plus an idempotency marker in one transaction.
 * Consequences:
 *   + Retry-safe order creation and authoritative totals.
 *   + Stock and product changes are checked atomically.
 *   - Requires Functions deployment and Firebase Rules/claim configuration.
 */

import { createHash } from "node:crypto";

import { initializeApp } from "firebase-admin/app";
import { FieldValue, getFirestore } from "firebase-admin/firestore";
import { HttpsError, onCall } from "firebase-functions/v2/https";
import { logger } from "firebase-functions";

initializeApp();
const db = getFirestore();

const REGION = "europe-west1";
const VALID_PURPOSES = new Set(["personal", "gift"]);
const VALID_DELIVERY_TYPES = new Set(["stop_desk", "domicile"]);

type RawCartItem = {
  id?: unknown;
  qty?: unknown;
  purchase_purpose?: unknown;
};

type GiftInput = {
  source?: unknown;
  recipient_name?: unknown;
  recipient_phone?: unknown;
  recipient_type?: unknown;
  occasion?: unknown;
  message?: unknown;
  budget?: unknown;
  mood?: unknown;
  sender_name?: unknown;
  anonymous?: unknown;
};

type CheckoutPayload = {
  customer?: Record<string, unknown>;
  cart?: RawCartItem[];
  gift?: GiftInput | null;
  wilaya?: unknown;
  delivery_type?: unknown;
  idempotencyKey?: unknown;
};

type Product = {
  id: string;
  title?: string;
  price?: number;
  img?: string;
  active?: boolean;
  archived?: boolean;
  stock_quantity?: number;
  availability_type?: "in_stock" | "on_demand";
  giftable?: boolean;
  lead_time_min_days?: number;
  lead_time_max_days?: number;
  lead_time_days?: number;
};

type OrderItem = {
  id: string;
  title: string;
  price: number;
  qty: number;
  img: string;
  availability_type: "in_stock" | "on_demand";
  lead_time_min_days: number;
  lead_time_max_days: number;
  purchase_purpose: "personal" | "gift";
};

function asString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function asPositiveInt(value: unknown): number {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 0;
}

function digits(value: string): string {
  return value.replace(/\D/g, "");
}

function idempotencyDocumentId(key: string): string {
  return createHash("sha256").update(key, "utf8").digest("hex");
}

function requireIdempotencyKey(value: unknown): string {
  const key = asString(value);
  if (key.length < 16 || key.length > 128) {
    throw new HttpsError("invalid-argument", "مفتاح الطلب غير صالح.");
  }
  return key;
}

function requireCart(value: unknown): RawCartItem[] {
  if (!Array.isArray(value) || value.length === 0 || value.length > 100) {
    throw new HttpsError("invalid-argument", "السلة فارغة أو تتجاوز الحد المسموح.");
  }
  return value;
}

function normalizeStatusMessage(error: unknown): string {
  return error instanceof Error ? error.message : "unknown_error";
}

export const createOrder = onCall(
  {
    region: REGION,
    timeoutSeconds: 30,
    memory: "256MiB",
    enforceAppCheck: false,
  },
  async (request) => {
    const requestId = asString(request.rawRequest?.header("x-request-id")) || `req_${Date.now()}`;
    const data = (request.data || {}) as CheckoutPayload;
    const idempotencyKey = requireIdempotencyKey(data.idempotencyKey);
    const cartInput = requireCart(data.cart);
    const customer = data.customer && typeof data.customer === "object" ? data.customer : {};
    const deliveryType = asString(data.delivery_type) || "stop_desk";
    const wilayaNum = Number(data.wilaya);

    if (!VALID_DELIVERY_TYPES.has(deliveryType) || !Number.isInteger(wilayaNum)) {
      throw new HttpsError("invalid-argument", "بيانات التوصيل غير صالحة.");
    }

    const idempotencyRef = db.collection("orderIdempotency").doc(idempotencyDocumentId(idempotencyKey));
    const orderRef = db.collection("orders").doc();

    try {
      const result = await db.runTransaction(async (transaction) => {
        const existingMarker = await transaction.get(idempotencyRef);
        if (existingMarker.exists) {
          return { orderId: existingMarker.get("orderId") as string, reused: true };
        }

        const settingsSnapshot = await transaction.get(db.doc("settings/public"));
        const features = (settingsSnapshot.data()?.features || {}) as Record<string, unknown>;
        const giftsEnabled = features.gifts !== false;

        const productIds = cartInput.map((item) => asString(item.id));
        if (productIds.some((id) => !id) || new Set(productIds).size !== productIds.length) {
          throw new HttpsError("invalid-argument", "تحتوي السلة على كتاب مكرر أو غير صالح.");
        }

        const productSnapshots = await Promise.all(
          productIds.map((id) => transaction.get(db.collection("products").doc(id))),
        );
        const items: OrderItem[] = [];
        const quantities = new Map<string, number>();

        for (let index = 0; index < productSnapshots.length; index += 1) {
          const snapshot = productSnapshots[index];
          const raw = snapshot.data() as Product | undefined;
          const input = cartInput[index];
          const productId = productIds[index];
          const quantity = asPositiveInt(input.qty);
          const purpose = asString(input.purchase_purpose) || "personal";

          if (!snapshot.exists || !raw || raw.active === false || raw.archived === true) {
            throw new HttpsError("failed-precondition", "أحد الكتب لم يعد متاحًا.");
          }
          if (quantity < 1 || quantity > 20 || !VALID_PURPOSES.has(purpose)) {
            throw new HttpsError("invalid-argument", "بيانات أحد الكتب غير صالحة.");
          }
          if (purpose === "gift" && (!giftsEnabled || raw.giftable === false)) {
            throw new HttpsError("failed-precondition", "لا يمكن إهداء أحد الكتب المحددة.");
          }

          const availability = raw.availability_type === "on_demand" ? "on_demand" : "in_stock";
          const minimum = Math.max(0, Math.min(1, Number(raw.lead_time_min_days ?? raw.lead_time_days ?? 0)));
          const maximum = Math.max(minimum, Math.min(1, Number(raw.lead_time_max_days ?? raw.lead_time_days ?? 0)));
          const price = Number(raw.price);
          if (!Number.isInteger(price) || price <= 0) {
            throw new HttpsError("failed-precondition", "سعر أحد الكتب غير صالح.");
          }

          quantities.set(productId, quantity);
          items.push({
            id: productId,
            title: asString(raw.title),
            price,
            qty: quantity,
            img: asString(raw.img),
            availability_type: availability,
            lead_time_min_days: minimum,
            lead_time_max_days: maximum,
            purchase_purpose: purpose as "personal" | "gift",
          });
        }

        const giftItems = items.filter((item) => item.purchase_purpose === "gift");
        const gift = data.gift && typeof data.gift === "object" ? data.gift : null;
        if (giftItems.length > 0) {
          if (!gift) {
            throw new HttpsError("invalid-argument", "بيانات الهدية مطلوبة.");
          }
          const recipientName = asString(gift.recipient_name);
          const recipientPhone = asString(gift.recipient_phone);
          if (!recipientName || digits(recipientPhone).length < 8) {
            throw new HttpsError("invalid-argument", "اسم المستلم ورقم هاتفه مطلوبان.");
          }
        } else if (gift) {
          throw new HttpsError("invalid-argument", "لا يمكن إرسال تفاصيل هدية دون كتاب مهدي.");
        }

        const feeQuery = db.collection("deliveryFees").where("num", "==", wilayaNum).limit(1);
        const feeSnapshot = await transaction.get(feeQuery);
        if (feeSnapshot.empty) {
          throw new HttpsError("failed-precondition", "التوصيل غير متاح إلى الولاية المحددة.");
        }
        const feeData = feeSnapshot.docs[0].data() as Record<string, unknown>;
        const fee = Number(feeData[deliveryType]);
        if (!Number.isInteger(fee) || fee < 0) {
          throw new HttpsError("failed-precondition", "نوع التوصيل المحدد غير متاح.");
        }
        if (deliveryType === "domicile" && !asString(customer.address)) {
          throw new HttpsError("invalid-argument", "عنوان التوصيل إلى المنزل مطلوب.");
        }

        for (const item of items) {
          if (item.availability_type !== "in_stock") continue;
          const snapshot = productSnapshots.find((candidate) => candidate.id === item.id);
          const currentStock = Number(snapshot?.get("stock_quantity") ?? 0);
          const requested = quantities.get(item.id) ?? 0;
          if (!Number.isInteger(currentStock) || currentStock < requested) {
            throw new HttpsError("failed-precondition", "الكمية المطلوبة من أحد الكتب غير متاحة.");
          }
          transaction.update(db.collection("products").doc(item.id), {
            stock_quantity: currentStock - requested,
            updatedAt: FieldValue.serverTimestamp(),
          });
        }

        const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
        const total = subtotal + fee;
        const order = {
          id: orderRef.id,
          status: "new",
          items,
          gift: giftItems.length > 0 ? {
            source: asString(gift?.source) || "cart",
            recipient_name: asString(gift?.recipient_name),
            recipient_phone: asString(gift?.recipient_phone),
            recipient_type: asString(gift?.recipient_type) || "friend",
            occasion: asString(gift?.occasion) || "general",
            message: asString(gift?.message),
            budget: Number(gift?.budget) || 0,
            mood: asString(gift?.mood) || "warm",
            sender_name: asString(gift?.sender_name || customer.name),
            anonymous: gift?.anonymous === true,
            gift_item_ids: giftItems.map((item) => item.id),
          } : null,
          customer,
          delivery: { wilaya: wilayaNum, delivery_type: deliveryType },
          subtotal,
          deliveryFee: fee,
          total,
          currency: "DZD",
          idempotencyKey,
          source: "cloudflare-pages",
          createdAt: FieldValue.serverTimestamp(),
          updatedAt: FieldValue.serverTimestamp(),
          schemaVersion: 1,
          requestId,
        };

        transaction.create(orderRef, order);
        transaction.create(idempotencyRef, {
          orderId: orderRef.id,
          createdAt: FieldValue.serverTimestamp(),
          expiresAt: null,
        });
        return { orderId: orderRef.id, reused: false };
      });

      logger.info("order_created_or_reused", {
        requestId,
        orderId: result.orderId,
        reused: result.reused,
      });
      return { ok: true, orderId: result.orderId, reused: result.reused, requestId };
    } catch (error) {
      if (error instanceof HttpsError) throw error;
      logger.error("order_creation_failed", {
        requestId,
        error: normalizeStatusMessage(error),
      });
      throw new HttpsError("internal", "تعذر إنشاء الطلب حاليًا.", { requestId });
    }
  },
);
