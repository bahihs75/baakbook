import type { PagesFunction } from "@cloudflare/workers-types";
import { callTrustedCallable } from "../_shared/trusted";
import { errorResponse, handleOptions, readJson, type BaakEnv } from "../_shared/http";

type OrdersRoute = PagesFunction<BaakEnv>;

export const onRequestOptions: OrdersRoute = async ({ request, env }) => handleOptions(request, env);

export const onRequestPost: OrdersRoute = async ({ request, env }) => {
  const body = await readJson(request);
  const cart = body.cart;
  if (!Array.isArray(cart) || cart.length === 0) {
    return errorResponse("CART_INVALID", "السلة فارغة أو غير صالحة.", request, env, 422);
  }
  const headerKey = request.headers.get("Idempotency-Key")?.trim();
  const bodyKey = typeof body.idempotencyKey === "string" ? body.idempotencyKey.trim() : "";
  const idempotencyKey = headerKey || bodyKey || crypto.randomUUID();
  return callTrustedCallable(request, env, env.TRUSTED_ORDER_FUNCTION_URL, {
    ...body,
    idempotencyKey,
  });
};

export const onRequest: OrdersRoute = async ({ request, env }) => {
  if (request.method === "OPTIONS") return handleOptions(request, env);
  return errorResponse("METHOD_NOT_ALLOWED", "طريقة الطلب غير مدعومة.", request, env, 405, { allowed: ["POST"] });
};
