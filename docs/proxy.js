/**
 * 米游社扫码登录 CORS 代理 - Cloudflare Worker（透明转发版）
 *
 * 更新方法：
 *   Cloudflare Dashboard -> Workers -> 你的 Worker -> Edit Code ->
 *   全选删除，粘贴本文件全部代码 -> Deploy
 *
 * 安全说明：
 *   - 仅转发白名单内的 3 个米哈游 passport 接口，无日志、无存储
 *   - Cookie 只在浏览器内组装；stoken 仅在请求 cookie_token 时经由本代理中转一次
 *   - /_debug 为诊断路径，仅回显收到的请求内容，可随时删除
 */

const UPSTREAMS = [
  { prefix: "/account/", host: "https://passport-api.mihoyo.com" },
  { prefix: "/apihub/", host: "https://bbs-api.miyoushe.com" },
  { prefix: "/user/", host: "https://bbs-api.miyoushe.com" },
  { prefix: "/post/", host: "https://bbs-api.miyoushe.com" },
];

const ALLOWED_PATHS = new Set([
  "/account/ma-cn-passport/app/createQRLogin",
  "/account/ma-cn-passport/app/queryQRLoginStatus",
  "/account/auth/api/getCookieAccountInfoBySToken",
  "/apihub/app/api/signIn",
  "/user/api/getUserFullInfo",
]);

// 不应转发给上游的请求头（cookie 必须保留：bbs-api 靠它认证）
const HOP_HEADERS = ["host", "origin", "referer", "content-length", "connection"];

function corsHeaders(contentType) {
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, x-rpc-device_id",
    "Access-Control-Max-Age": "86400",
  };
  if (contentType) headers["Content-Type"] = contentType;
  return headers;
}

function buildOutgoingHeaders(request) {
  // 透明透传浏览器请求头，仅删除逐跳头，并补齐米哈游必需的默认值
  const headers = new Headers(request.headers);
  HOP_HEADERS.forEach((h) => headers.delete(h));
  if (!headers.has("User-Agent")) headers.set("User-Agent", "HYPContainer/1.3.3.182");
  if (!headers.has("x-rpc-app_id")) headers.set("x-rpc-app_id", "ddxf5dufpuyo");
  if (!headers.has("x-rpc-client_type")) headers.set("x-rpc-client_type", "3");
  if (!headers.has("x-rpc-device_id"))
    headers.set("x-rpc-device_id", crypto.randomUUID().replace(/-/g, "").slice(0, 16));
  return headers;
}

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    const url = new URL(request.url);

    // 诊断路径：回显实际收到的请求与将要转发的头
    if (url.pathname === "/_debug") {
      const incomingBody = request.method === "POST" ? await request.text() : "(no body)";
      const outgoing = buildOutgoingHeaders(request);
      return new Response(
        JSON.stringify(
          {
            method: request.method,
            incoming_body_length: incomingBody.length,
            incoming_body_sample: incomingBody.slice(0, 200),
            outgoing_headers: Object.fromEntries(outgoing.entries()),
          },
          null,
          2,
        ),
        { status: 200, headers: corsHeaders("application/json") },
      );
    }

    const route = UPSTREAMS.find((r) => url.pathname.startsWith(r.prefix));
    if (!route || !ALLOWED_PATHS.has(url.pathname)) {
      return new Response("Not Found", { status: 404, headers: corsHeaders() });
    }
    if (request.method !== "POST" && request.method !== "GET") {
      return new Response("Method Not Allowed", { status: 405, headers: corsHeaders() });
    }

    const hasBody = request.method === "POST";

    let upstream;
    try {
      upstream = await fetch(route.host + url.pathname + url.search, {
        method: request.method,
        headers: buildOutgoingHeaders(request),
        body: hasBody ? request.body : undefined,
      });
    } catch (err) {
      return new Response(JSON.stringify({ retcode: -1, message: "upstream error: " + err.message }), {
        status: 502,
        headers: corsHeaders("application/json"),
      });
    }

    const respHeaders = corsHeaders(upstream.headers.get("Content-Type") || "application/json");

    // 透传上游业务头（如 x-rpc-aigis），便于排查风控
    for (const name of ["x-rpc-aigis", "x-trace-id"]) {
      const v = upstream.headers.get(name);
      if (v) respHeaders[name] = v;
    }

    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: respHeaders,
    });
  },
};
