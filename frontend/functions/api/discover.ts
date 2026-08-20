import type { PagesFunction } from "@cloudflare/workers-types";
import { listDocuments } from "../_shared/firestore";
import { errorResponse, handleOptions, jsonResponse, readJson, type BaakEnv } from "../_shared/http";

type DiscoverRoute = PagesFunction<BaakEnv>;

type DiscoverInput = {
  goal?: unknown;
  pace?: unknown;
  mood?: unknown;
};

type Profile = {
  label: string;
  categories?: string[];
  keywords: string[];
};

const goalProfiles: Record<string, Profile> = {
  story: { label: "حكاية تأخذك بعيدًا", categories: ["روايات"], keywords: ["رواية", "قصة", "شخصيات", "أحداث"] },
  growth: { label: "خطوة عملية إلى الأمام", categories: ["تنمية بشرية"], keywords: ["عادات", "نجاح", "تطوير", "تحسين", "صلاة"] },
  knowledge: { label: "فكرة جديدة تتعلمها", categories: ["علوم", "تاريخ"], keywords: ["علم", "تاريخ", "معرفة", "مجتمع", "اكتشاف"] },
  escape: { label: "عالم مختلف تعيشه", categories: ["روايات"], keywords: ["خيال", "مملكة", "عالم", "مخلوقات", "مغامرة", "ضباب"] },
};

const moodProfiles: Record<string, Profile> = {
  mystery: { label: "الغموض والتشويق", keywords: ["غموض", "جريمة", "قاتل", "أسرار", "سر", "خطر", "نفسي", "اضطراب"] },
  romance: { label: "الرومانسية والمشاعر", keywords: ["حب", "رومانسية", "عاطفية", "علاقة", "حبيب", "مشاعر"] },
  fantasy: { label: "الخيال والعوالم غير المألوفة", keywords: ["خيال", "مملكة", "مخلوقات", "مصاص", "ضباب", "سحر", "عالم"] },
  change: { label: "التغيير والتحسن", keywords: ["عادات", "نجاح", "تحسين", "تطوير", "حياة", "عملية"] },
};

function cleanInput(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function recommendation(product: Record<string, unknown> & { id: string }, input: Required<Record<keyof DiscoverInput, string>>): Record<string, unknown> {
  const goal = goalProfiles[input.goal] || goalProfiles.story;
  const mood = moodProfiles[input.mood] || moodProfiles.mystery;
  const title = String(product.title ?? "");
  const description = String(product.desc ?? product.description ?? "");
  const category = String(product.category ?? "");
  const text = `${title} ${description} ${category}`;
  let score = 0;
  const goalMatches: string[] = [];
  const moodMatches: string[] = [];

  if (goal.categories?.includes(category)) {
    score += 6;
    goalMatches.push(goal.label);
  }
  for (const keyword of goal.keywords) {
    if (text.includes(keyword)) {
      score += 1.2;
      goalMatches.push(keyword);
    }
  }
  for (const keyword of mood.keywords) {
    if (text.includes(keyword)) {
      score += 1.6;
      moodMatches.push(keyword);
    }
  }
  const descriptionSize = description.length;
  score += input.pace === "quick" ? Math.max(0, 2.5 - descriptionSize / 500) : Math.min(2.5, descriptionSize / 500);
  const reasons: string[] = [];
  if (goalMatches.length) reasons.push(`يلتقي مع رغبتك في ${goal.label}`);
  if (moodMatches.length) reasons.push(`يحمل نبرة من ${mood.label}`);
  reasons.push(input.pace === "quick" ? "مناسب لبداية خفيفة وسريعة" : "يمنحك مساحة أكبر للتفاصيل والاندماج");
  return {
    ...product,
    score,
    reason: [...new Set(reasons)].join("، "),
  };
}

export const onRequestOptions: DiscoverRoute = async ({ request, env }) => handleOptions(request, env);

export const onRequestPost: DiscoverRoute = async ({ request, env }) => {
  const input = await readJson(request) as DiscoverInput;
  const preferences = {
    goal: cleanInput(input.goal),
    pace: cleanInput(input.pace),
    mood: cleanInput(input.mood),
  };
  if (!preferences.goal || !preferences.pace || !preferences.mood) {
    return errorResponse("DISCOVERY_INPUT_INVALID", "اختر إجابات الأسئلة الثلاثة أولًا.", request, env, 422);
  }
  try {
    const products = await listDocuments("products", env, {
      limit: 100,
      filters: [{ fieldPath: "active", value: true }, { fieldPath: "archived", value: false }],
    });
    const recommendations = products
      .filter((product) => Number(product.stock_quantity ?? 0) > 0 && product.discoverable !== false)
      .map((product) => recommendation(product, preferences))
      .sort((left, right) => Number(right.score) - Number(left.score) || String(left.title).localeCompare(String(right.title), "ar"))
      .slice(0, 3);
    return jsonResponse({ recommendations }, request, env);
  } catch (error) {
    console.error("discovery_failed", error);
    return errorResponse("DISCOVERY_UNAVAILABLE", "تعذر إعداد الاقتراحات حاليًا.", request, env, 503);
  }
};
