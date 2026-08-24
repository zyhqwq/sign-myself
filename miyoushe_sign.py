#!/usr/bin/env python3
"""米游社每日签到脚本 - GitHub Actions 专用版

使用 MIYOUSHE_COOKIE（由本地 miyoushe_qr_login.py 扫码获取）完成
米游社各游戏板块的社区签到，领取米游币。

参考实现：
- TimeRainStarSky/TRSS-Plugin (Apps/miHoYoLogin.js) 扫码登录与请求头
- starudream/sign-task 签到接口 (apihub/app/api/signIn) 与 DS 签名
"""

import hashlib
import json
import os
import random
import string
import sys
import time
from datetime import datetime

import requests

from notify import send_notification, print_notify_results

# ================== 接口地址（bbs 社区） ==================
SIGN_URL = "https://bbs-api.miyoushe.com/apihub/app/api/signIn"
SIGN_STATUS_URL = "https://bbs-api.miyoushe.com/apihub/sapi/querySignInStatus"
USER_INFO_URL = "https://bbs-api.miyoushe.com/user/api/getUserFullInfo"

# ================== DS 签名盐值 ==================
# https://github.com/UIGF-org/mihoyo-api-collect
DS_SALT_K2 = "QVu5OdwEWxkq9ygpYBgDprR5tI471HWQ"   # DS1：无参数签名
DS_SALT_6X = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"   # DS2：body + query 签名

APP_VERSION = "2.81.1"
APP_ID = "bll8iq97cem8"

# 游戏板块 ID（gids）
GAMES = {
    "1": "崩坏3",
    "2": "原神",
    "3": "崩坏学园2",
    "4": "未定事件簿",
    "6": "崩坏:星穹铁道",
    "8": "绝区零",
}
DEFAULT_GIDS = ["1", "2", "4", "6", "8"]

COOKIE_ENV = "MIYOUSHE_COOKIE"


def random_string(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def ds1():
    """DS 签名（无 body/query 参与）"""
    t = int(time.time())
    r = random_string(6)
    return f"{t},{r},{md5(f'salt={DS_SALT_K2}&t={t}&r={r}')}"


def ds2(body="", query=""):
    """DS 签名（body + query 参与），用于签到接口"""
    t = int(time.time())
    r = random.randint(100001, 199999)
    return f"{t},{r},{md5(f'salt={DS_SALT_6X}&t={t}&r={r}&b={body}&q={query}')}"


def bbs_headers(cookie_str, ds=None, extra=None):
    headers = {
        "Accept-Encoding": "gzip",
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; 22011211C Build/TP1A.220624.014; wv) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 "
            f"Mobile Safari/537.36 miHoYoBBS/{APP_VERSION}"
        ),
        "Referer": "https://app.mihoyo.com",
        "x-rpc-app_version": APP_VERSION,
        "x-rpc-app_id": APP_ID,
        "x-rpc-verify_key": APP_ID,
        "x-rpc-client_type": "2",
        "x-rpc-device_id": random_string(16),
        "x-rpc-device_name": random_string(16),
        "x-rpc-device_model": random_string(16),
        "x-rpc-sys_version": "12",
        "x-rpc-channel": "mihoyo",
        "Cookie": cookie_str,
    }
    if ds:
        headers["DS"] = ds
    if extra:
        headers.update(extra)
    return headers


def parse_cookie(cookie_str):
    """解析 Cookie 字符串为字典"""
    cookies = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def bbs_get(url, params, cookie_str):
    resp = requests.get(
        url,
        params=params,
        headers=bbs_headers(cookie_str, ds=ds1()),
        timeout=15,
    )
    return resp.json()


def bbs_post_sign(gid, cookie_str):
    body = json.dumps({"gids": gid}, separators=(",", ":"))
    resp = requests.post(
        SIGN_URL,
        data=body,
        headers=bbs_headers(cookie_str, ds=ds2(body)),
        timeout=15,
    )
    return resp.json()


def get_nickname(cookies, cookie_str):
    """获取账号昵称（仅用于通知展示，失败不影响签到）"""
    uid = cookies.get("stuid") or cookies.get("ltuid")
    if not uid:
        return ""
    try:
        data = bbs_get(USER_INFO_URL, {"uid": uid}, cookie_str)
        if data.get("retcode") == 0:
            return data["data"]["user_info"].get("nickname", "")
    except Exception:
        pass
    return ""


def sign_forum(gid, name, cookie_str):
    """对单个板块执行签到，返回结果行"""
    status = bbs_get(SIGN_STATUS_URL, {"gids": gid}, cookie_str)

    if status.get("retcode") == -100 or status.get("message") == "登录失效，请重新登录":
        return {"line": f"{name}: Cookie 已失效，请重新扫码获取", "ok": False}

    if status.get("retcode") == 0 and status.get("data", {}).get("is_signed"):
        return {"line": f"{name}: 今天已签到", "ok": True}

    result = bbs_post_sign(gid, cookie_str)
    retcode = result.get("retcode")

    if retcode == 0:
        points = result.get("data", {}).get("points")
        award = f"，获得 {points} 米游币" if isinstance(points, int) else ""
        return {"line": f"{name}: 签到成功{award}", "ok": True}

    msg = result.get("message", "未知错误")
    if retcode in (-100, -101):
        return {"line": f"{name}: Cookie 已失效，请重新扫码获取", "ok": False}
    if retcode == 1034 or "验证" in msg:
        return {"line": f"{name}: 触发风控验证，签到失败 ({msg})", "ok": False}

    # 其余错误视为已签或临时失败，不再重试
    already = ("已签" in msg) or ("repeat" in msg.lower())
    ok = already
    line = f"{name}: 今天已签到" if already else f"{name}: 签到失败 - {msg} (retcode={retcode})"
    return {"line": line, "ok": ok}


def process_account(idx, cookie_str):
    cookies = parse_cookie(cookie_str)
    if not cookies.get("stoken"):
        return [f"账号_{idx}: Cookie 缺少 stoken 字段，请重新扫码获取"], False

    nickname = get_nickname(cookies, cookie_str)
    label = f"{nickname}" if nickname else f"账号_{idx}"

    gids_env = os.environ.get("MIYOUSHE_GIDS", "").strip()
    gids = [g.strip() for g in gids_env.split(",") if g.strip() in GAMES] if gids_env else DEFAULT_GIDS

    lines, all_ok = [], True
    for gid in gids:
        try:
            r = sign_forum(gid, GAMES[gid], cookie_str)
        except Exception as e:
            r = {"line": f"{GAMES[gid]}: 请求异常 - {e}", "ok": False}
        lines.append(r["line"])
        print(r["line"])
        all_ok = all_ok and r["ok"]
    return lines, all_ok


def main():
    print(f"[米游社签到] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    raw = os.environ.get(COOKIE_ENV, "").strip()
    if not raw:
        msg = f"错误: 未设置 {COOKIE_ENV}（请在本地运行 miyoushe_qr_login.py 扫码获取）"
        print(msg)
        print_notify_results(send_notification("米游社签到失败", msg))
        sys.exit(1)

    account_list = [c.strip() for c in raw.split(",") if c.strip()]
    print(f"共 {len(account_list)} 个账号")

    results, all_ok = [], True
    for idx, cookie_str in enumerate(account_list, 1):
        print(f"\n--- 账号{idx} ---")
        lines, ok = process_account(idx, cookie_str)
        results.extend(lines)
        all_ok = all_ok and ok

    report = "\n".join(results)
    title = "米游社签到成功" if all_ok else "米游社签到部分失败"
    print(f"\n{report}")
    print_notify_results(send_notification(title, report))

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
