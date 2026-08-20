import type { PagesFunction } from "@cloudflare/workers-types";
import { proxyTrustedAdmin } from "./trusted";
import { errorResponse, handleOptions, type BaakEnv } from "./http";

export type AdminRoute = PagesFunction<BaakEnv>;

export function adminHandler(path: string): AdminRoute {
  return async ({ request, env }) => {
    if (request.method === "OPTIONS") return handleOptions(request, env);
    if (!path) return errorResponse("ADMIN_ROUTE_INVALID", "مسار الإدارة غير صالح.", request, env, 400);
    return proxyTrustedAdmin(request, env, path);
  };
}
