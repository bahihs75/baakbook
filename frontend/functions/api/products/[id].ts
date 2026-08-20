import type { PagesFunction } from "@cloudflare/workers-types";
import { getDocument, listDocuments } from "../../_shared/firestore";
import { errorResponse, handleOptions, jsonResponse, type BaakEnv } from "../../_shared/http";
import { productPayloadForTest } from "../products";

type ProductDetailRoute = PagesFunction<BaakEnv>;

export const onRequestOptions: ProductDetailRoute = async ({ request, env }) => handleOptions(request, env);

export const onRequestGet: ProductDetailRoute = async ({ request, env, params }) => {
  const id = String(params.id || "").trim();
  if (!id) return errorResponse("INVALID_PRODUCT_ID", "معرّف الكتاب غير صالح.", request, env, 400);
  try {
    // Read by the document name first; this is the fastest and most reliable
    // path for the imported catalog. Some legacy documents use a different
    // Firestore name and keep the public code in the `id` field, so the query
    // below remains as a compatibility fallback.
    let product: (Record<string, unknown> & { id: string }) | null = null;
    try {
      product = await getDocument("products", id, env);
    } catch (error) {
      if (!String(error).includes("status 403") && !String(error).includes("status 404")) throw error;
    }
    if (!product) {
      // The public catalog query is already permitted by the current Firestore
      // rules. Match the legacy public code in memory instead of issuing a
      // composite equality query that may require an index or be rejected.
      const matches = await listDocuments("products", env, {
        limit: 100,
        filters: [{ fieldPath: "active", value: true }, { fieldPath: "archived", value: false }],
      });
      product = matches.find((item) => item.id === id) || null;
    }
    if (!product || product.active === false || product.archived === true) {
      return errorResponse("PRODUCT_NOT_FOUND", "لم نعثر على الكتاب المطلوب.", request, env, 404);
    }
    return jsonResponse(productPayloadForTest(product), request, env);
  } catch (error) {
    console.error("public_product_failed", error);
    return errorResponse("PRODUCT_UNAVAILABLE", "تعذر تحميل الكتاب حاليًا.", request, env, 503);
  }
};
