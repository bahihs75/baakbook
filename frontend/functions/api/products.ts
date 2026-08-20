import type { PagesFunction } from "@cloudflare/workers-types";
import { decodeFirestoreValue, listDocuments, type FirestoreDocument } from "../_shared/firestore";
import { errorResponse, handleOptions, jsonResponse, type BaakEnv } from "../_shared/http";

function productPayload(product: Record<string, unknown> & { id: string }): Record<string, unknown> {
  const legacy = product.legacyPayload && typeof product.legacyPayload === "object"
    ? product.legacyPayload as Record<string, unknown>
    : {};
  const tags = Array.isArray(product.discovery_tags)
    ? product.discovery_tags
    : Array.isArray(product.discoveryTags)
      ? product.discoveryTags
      : Array.isArray(product.gift_tags)
        ? product.gift_tags
        : Array.isArray(product.giftTags)
          ? product.giftTags
          : [];
  const availability = product.availability_type === "on_demand" ? "on_demand" : "in_stock";
  const leadTime = Number(product.lead_time_days ?? product.leadTimeDays ?? product.lead_time_max_days ?? 0);
  return {
    id: product.id,
    title: String(product.title ?? ""),
    author: String(product.author ?? legacy.author ?? ""),
    desc: String(product.desc ?? product.description ?? legacy.desc ?? legacy.description ?? ""),
    price: Number(product.price ?? 0),
    stock_quantity: Number(product.stock_quantity ?? product.stockQuantity ?? 0),
    availability_type: availability,
    lead_time_min_days: Number(product.lead_time_min_days ?? product.leadTimeMinDays ?? leadTime),
    lead_time_max_days: Number(product.lead_time_max_days ?? product.leadTimeMaxDays ?? leadTime),
    lead_time_days: leadTime,
    img: String(product.img ?? product.image_url ?? product.imageUrl ?? ""),
    category: String(product.category ?? product.category_name ?? product.categorySlug ?? ""),
    giftable: product.giftable !== false,
    discoverable: product.discoverable !== false,
    featured: product.featured === true,
    active: product.active !== false,
    discovery_tags: tags,
    gift_tags: tags,
  };
}

export type ProductRoute = PagesFunction<BaakEnv>;

export const onRequestOptions: ProductRoute = async ({ request, env }) => handleOptions(request, env);

export const onRequestGet: ProductRoute = async ({ request, env }) => {
  try {
    const documents = await listDocuments("products", env, {
      limit: 100,
      filters: [{ fieldPath: "active", value: true }, { fieldPath: "archived", value: false }],
    });
    const products = documents
      .filter((item) => item.active !== false && item.archived !== true)
      .map(productPayload);
    return jsonResponse(products, request, env);
  } catch (error) {
    console.error("public_products_failed", error);
    return errorResponse("CATALOG_UNAVAILABLE", "تعذر تحميل الكتب حاليًا.", request, env, 503);
  }
};

export function productPayloadForTest(product: Record<string, unknown> & { id: string }): Record<string, unknown> {
  return productPayload(product);
}
