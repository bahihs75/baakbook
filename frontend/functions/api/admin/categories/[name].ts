import { adminHandler, type AdminRoute } from "../../../_shared/admin-route";

export const onRequest: AdminRoute = async (context) => {
  const name = encodeURIComponent(String(context.params.name || "").trim());
  return adminHandler(name ? `categories/${name}` : "")(context);
};
