import type { PagesFunction } from "@cloudflare/workers-types";
import { getDocument } from "../_shared/firestore";
import { errorResponse, handleOptions, jsonResponse, type BaakEnv } from "../_shared/http";

type SettingsRoute = PagesFunction<BaakEnv>;

export const onRequestOptions: SettingsRoute = async ({ request, env }) => handleOptions(request, env);

export const onRequestGet: SettingsRoute = async ({ request, env }) => {
  try {
    const settings = await getDocument("settings", "public", env);
    const publicSettings = settings && typeof settings === "object"
      ? {
          features: settings.features && typeof settings.features === "object" ? settings.features : {},
          storefront: settings.storefront && typeof settings.storefront === "object" ? settings.storefront : {},
        }
      : { features: {}, storefront: {} };
    return jsonResponse(publicSettings, request, env);
  } catch (error) {
    console.error("public_settings_read_failed", error);
    return errorResponse("SETTINGS_UNAVAILABLE", "تعذر تحميل إعدادات المتجر حاليًا.", request, env, 503);
  }
};
