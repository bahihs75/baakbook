import type { PagesFunction } from "@cloudflare/workers-types";
import { getDocument } from "../../_shared/firestore";
import { errorResponse, handleOptions, jsonResponse, type BaakEnv } from "../../_shared/http";
import { productPayloadForTest } from "../products";

type ProductDetailRoute = PagesFunction<BaakEnv>;

export const onRequestOptions: ProductDetailRoute = async ({ request, env }) => handleOptions(request, env);

export const onRequestGet: ProductDetailRoute = async ({ request, env, params }) => {
  const id = String(params.id || "").trim();
  if (!id) return errorResponse("INVALID_PRODUCT_ID", "معرّف الكتاب غير صالح.", request, env, 400);
  try {
    const product = await getDocument("products", id, env);
    if (!product || product.active === false || product.archived === true) {
      return errorResponse("PRODUCT_NOT_FOUND", "لم نعثر على الكتاب المطلوب.", request, env, 404);
    }
    return jsonResponse(productPayloadForTest(product), request, env);
  } catch (error) {
    console.error("public_product_failed", error);
    return errorResponse("PRODUCT_UNAVAILABLE", "تعذر تحميل الكتاب حاليًا.", request, env, 503);
  }
};
