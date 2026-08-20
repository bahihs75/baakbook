import type { PagesFunction } from "@cloudflare/workers-types";
import { listTopLevelDocuments } from "../_shared/firestore";
import { errorResponse, handleOptions, jsonResponse, type BaakEnv } from "../_shared/http";

type CategoriesRoute = PagesFunction<BaakEnv>;

export const onRequestOptions: CategoriesRoute = async ({ request, env }) => handleOptions(request, env);

export const onRequestGet: CategoriesRoute = async ({ request, env }) => {
  try {
    const documents = await listTopLevelDocuments("categories", env, 100, [{ fieldPath: "active", value: true }]);
    const categories = documents
      .filter((item) => item.active !== false)
      .sort((left, right) => String(left.name ?? "").localeCompare(String(right.name ?? ""), "ar"));
    return jsonResponse(categories, request, env);
  } catch (error) {
    console.error("categories_read_failed", error);
    return errorResponse("CATEGORIES_UNAVAILABLE", "تعذر تحميل التصنيفات حاليًا.", request, env, 503);
  }
};
