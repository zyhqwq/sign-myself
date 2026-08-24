/**
 * 米游社扫码登录 CORS 代理 - Cloudflare Worker
 *
 * 部署方法：
 *   1. 打开 https://dash.cloudflare.com -> Workers & Pages -> Create Worker
 *   2. 把本文件全部代码粘贴进编辑器，Deploy
 *   3. 把得到的 https://xxx.xxx.workers.dev 填入 docs/index.html 页面的「代理设置」
 *
 * 安全说明：
 *   - 仅转发白名单内的 3 个米哈游 passport 接口，无日志、无存储
 *   - Cookie 只在浏览器内组装；stoken 仅在请求 cookie_token 时经由本代理中转一次
 */

const UPSTREAM = "https://passport-api.mihoyo.com";

const ALLOWED_PATHS = new Set([
  "/account/ma-cn-passport/app/createQRLogin",
  "/account/ma-cn-passport/app/queryQRLoginStatus",
  "/account/auth/api/getCookieAccountInfoBySToken",
]);

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

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    const url = new URL(request.url);
    if (!ALLOWED_PATHS.has(url.pathname)) {
      return new Response("Not Found", { status: 404, headers: corsHeaders() });
    }
    if (request.method !== "POST" && request.method !== "GET") {
      return new Response("Method Not Allowed", { status: 405, headers: corsHeaders() });
    }

    const headers = {
      "User-Agent": "HYPContainer/1.3.3.182",
      "x-rpc-app_id": "ddxf5dufpuyo",
      "x-rpc-client_type": "3",
    };

    // getCookieAccountInfoBySToken 需要 Cookie 头，由 query 参数转换而来
    const stoken = url.searchParams.get("stoken");
    if (stoken) {
      headers["Cookie"] =
        `stoken=${stoken};stuid=${url.searchParams.get("stuid") || ""};mid=${url.searchParams.get("mid") || ""}`;
    }
    if (request.method === "POST") {
      headers["Content-Type"] = "application/json";
    }

    let upstream;
    try {
      upstream = await fetch(UPSTREAM + url.pathname + url.search, {
        method: request.method,
        headers,
        body: request.method === "POST" ? await request.text() : undefined,
      });
    } catch (err) {
      return new Response(JSON.stringify({ retcode: -1, message: "upstream error" }), {
        status: 502,
        headers: corsHeaders("application/json"),
      });
    }

    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: corsHeaders(upstream.headers.get("Content-Type") || "application/json"),
    });
  },
};
