import type { PagesFunction } from "@cloudflare/workers-types";
import { listTopLevelDocuments } from "../_shared/firestore";
import { errorResponse, handleOptions, jsonResponse, type BaakEnv } from "../_shared/http";

type DeliveryFeesRoute = PagesFunction<BaakEnv>;

export const onRequestOptions: DeliveryFeesRoute = async ({ request, env }) => handleOptions(request, env);

export const onRequestGet: DeliveryFeesRoute = async ({ request, env }) => {
  try {
    const documents = await listTopLevelDocuments("deliveryFees", env, 100);
    const fees = documents.sort((left, right) => Number(left.num ?? 0) - Number(right.num ?? 0));
    return jsonResponse(fees, request, env);
  } catch (error) {
    console.error("delivery_fees_read_failed", error);
    return errorResponse("DELIVERY_FEES_UNAVAILABLE", "تعذر تحميل رسوم التوصيل حاليًا.", request, env, 503);
  }
};
