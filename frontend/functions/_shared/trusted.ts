import { bearerToken, errorResponse, getRequestId, jsonResponse, type BaakEnv } from "./http";

export async function callTrustedCallable(
  request: Request,
  env: BaakEnv,
  url: string | undefined,
  data: Record<string, unknown>,
): Promise<Response> {
  if (!url?.trim()) {
    return errorResponse("TRUSTED_BACKEND_NOT_CONFIGURED", "لم تُجهّز خدمة الطلبات الموثوقة بعد.", request, env, 503);
  }
  const requestId = getRequestId(request);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  const headers = new Headers({
    "content-type": "application/json",
    "x-request-id": requestId,
  });
  const token = bearerToken(request);
  if (token) headers.set("authorization", `Bearer ${token}`);
  try {
    const downstream = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({ data }),
      signal: controller.signal,
    });
    const payload: unknown = await downstream.json().catch(() => null);
    if (!downstream.ok) {
      const downstreamError = payload && typeof payload === "object" && "error" in payload
        ? (payload as { error?: unknown }).error
        : null;
      const message = downstreamError && typeof downstreamError === "object" && "message" in downstreamError
        ? String((downstreamError as { message?: unknown }).message || "تعذر تنفيذ العملية.")
        : "تعذر تنفيذ العملية حاليًا.";
      return errorResponse("TRUSTED_BACKEND_ERROR", message, request, env, downstream.status >= 500 ? 503 : 422);
    }
    const result = payload && typeof payload === "object" && "result" in payload
      ? (payload as { result?: unknown }).result
      : payload;
    return jsonResponse(result || { ok: true, requestId }, request, env, downstream.status === 201 ? 201 : 200);
  } catch (error) {
    console.error("trusted_callable_failed", error);
    return errorResponse("TRUSTED_BACKEND_UNAVAILABLE", "تعذر الوصول إلى خدمة الطلبات الموثوقة.", request, env, 503);
  } finally {
    clearTimeout(timeout);
  }
}

export async function proxyTrustedAdmin(
  request: Request,
  env: BaakEnv,
  path: string,
): Promise<Response> {
  const token = bearerToken(request);
  if (!token) return errorResponse("AUTH_REQUIRED", "يلزم تسجيل الدخول لإدارة المتجر.", request, env, 401);
  if (!env.TRUSTED_ADMIN_FUNCTION_URL?.trim()) {
    return errorResponse("TRUSTED_ADMIN_BACKEND_NOT_CONFIGURED", "لم تُجهّز خدمة الإدارة الموثوقة بعد.", request, env, 503);
  }
  const target = `${env.TRUSTED_ADMIN_FUNCTION_URL.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  const headers = new Headers({
    Authorization: `Bearer ${token}`,
    "x-request-id": getRequestId(request),
  });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  try {
    const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer();
    const downstream = await fetch(target, { method: request.method, headers, body, signal: controller.signal });
    const responseBody = await downstream.arrayBuffer();
    const responseHeaders = new Headers({
      "content-type": downstream.headers.get("content-type") || "application/json; charset=utf-8",
    });
    return new Response(responseBody, { status: downstream.status, headers: responseHeaders });
  } catch (error) {
    console.error("trusted_admin_proxy_failed", error);
    return errorResponse("TRUSTED_ADMIN_BACKEND_UNAVAILABLE", "تعذر الوصول إلى لوحة الإدارة حاليًا.", request, env, 503);
  } finally {
    clearTimeout(timeout);
  }
}
