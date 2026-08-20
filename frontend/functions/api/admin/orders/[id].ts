import { adminHandler, type AdminRoute } from "../../../_shared/admin-route";

export const onRequest: AdminRoute = async (context) => {
  const id = encodeURIComponent(String(context.params.id || "").trim());
  return adminHandler(id ? `orders/${id}` : "")(context);
};
