#!/usr/bin/env python3
"""米游社每日签到脚本 - GitHub Actions 专用版

使用 MIYOUSHE_COOKIE（由本地 miyoushe_qr_login.py 扫码获取）完成
米游社各游戏板块的社区签到，领取米游币。

参考实现：
- TimeRainStarSky/TRSS-Plugin (Apps/miHoYoLogin.js) 扫码登录与请求头
- Womsxd/MihoyoBBSTools 签到接口、DS 签名与请求头组合
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
# 可用 MIYOUSHE_BASE_URL 切换中继（如 Cloudflare Worker）以更换出口 IP
BASE_URL = os.environ.get("MIYOUSHE_BASE_URL", "https://bbs-api.miyoushe.com").rstrip("/")
SIGN_URL = f"{BASE_URL}/apihub/app/api/signIn"
USER_INFO_URL = f"{BASE_URL}/user/api/getUserFullInfo"

# ================== DS 签名盐值（与版本配对，参考 MihoyoBBSTools/setting.py） ==================
DS_SALT_K2 = "47f15f1b66bee46b816115d8e8e6ebb6"   # DS1：对应 2.109.0
DS_SALT_6X = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"   # DS2：body+query 签名（一般不变）

APP_VERSION = "2.109.0"
APP_ID = "bll8iq97cem8"

# 游戏板块 ID（gids）
GAMES = {
    "1": "崩坏3",
    "2": "原神",
    "3": "崩坏学园2",
    "4": "未定事件簿",
    "6": "崩坏:星穹铁道",
    "8": "绝区零",
    "9": "崩坏:因缘精灵",
    "10": "星布谷地",
}
DEFAULT_GIDS = ["1", "2", "4", "6", "8"]

COOKIE_ENV = "MIYOUSHE_COOKIE"


def random_string(n):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


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
    r = str(random.randint(100001, 200000))
    return f"{t},{r},{md5(f'salt={DS_SALT_6X}&t={t}&r={r}&b={body}&q={query}')}"


def bbs_headers(cookie_str):
    """与米游社 App 客户端一致的请求头（okhttp UA），签到接口必需"""
    return {
        "User-Agent": "okhttp/4.9.3",
        "Referer": "https://app.mihoyo.com",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json; charset=UTF-8",
        "x-rpc-app_version": APP_VERSION,
        "x-rpc-app_id": APP_ID,
        "x-rpc-verify_key": APP_ID,
        "x-rpc-client_type": "2",
        "x-rpc-device_id": random_string(16),
        "x-rpc-device_name": random_string(16),
        "x-rpc-device_model": random_string(16),
        "x-rpc-sys_version": "12",
        "x-rpc-channel": "miyousheluodi",
        "x-rpc-h265_supported": "1",
        "x-rpc-csm_source": "discussion",
        "Cookie": cookie_str,
    }


def parse_cookie(cookie_str):
    cookies = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def get_nickname(cookies, cookie_str):
    uid = cookies.get("stuid") or cookies.get("ltuid")
    if not uid:
        return ""
    try:
        resp = requests.get(
            USER_INFO_URL,
            params={"uid": uid},
            headers={**bbs_headers(cookie_str), "DS": ds1(), "Content-Type": "application/json"},
            timeout=15,
        )
        data = resp.json()
        if data.get("retcode") == 0:
            return data["data"]["user_info"].get("nickname", "")
    except Exception:
        pass
    return ""


def sign_forum(gid, name, cookie_str):
    """对单个板块执行签到（直接签到，不依赖已废弃的状态查询接口）"""
    body = json.dumps({"gids": gid}, separators=(",", ":"))
    headers = bbs_headers(cookie_str)
    headers["DS"] = ds2(body)

    result = requests.post(SIGN_URL, data=body, headers=headers, timeout=15).json()
    retcode = result.get("retcode")
    msg = result.get("message", "")

    if retcode == 0:
        points = result.get("data", {}).get("points")
        award = f"，获得 {points} 米游币" if isinstance(points, int) else ""
        return {"line": f"{name}: 签到成功{award}", "ok": True}

    if retcode == 1034 or "验证" in msg:
        return {"line": f"{name}: 触发风控验证，签到失败（可稍后重试或换 IP）", "ok": False}
    if retcode in (-100, -101):
        return {"line": f"{name}: Cookie 已失效，请重新扫码获取", "ok": False}

    already = ("已签" in msg) or ("repeat" in msg.lower()) or ("已经" in msg)
    if already:
        return {"line": f"{name}: 今天已签到", "ok": True}
    return {"line": f"{name}: 签到失败 - {msg} (retcode={retcode})", "ok": False}


def process_account(idx, cookie_str):
    cookies = parse_cookie(cookie_str)
    if not cookies.get("stoken"):
        return [f"账号_{idx}: Cookie 缺少 stoken 字段，请重新扫码获取"], False

    nickname = get_nickname(cookies, cookie_str)
    label = nickname if nickname else f"账号_{idx}"
    print(f"账号: {label}")

    gids_env = os.environ.get("MIYOUSHE_GIDS", "").strip()
    gids = [g.strip() for g in gids_env.split(",") if g.strip() in GAMES] if gids_env else DEFAULT_GIDS

    lines, all_ok = [], True
    for i, gid in enumerate(gids):
        try:
            r = sign_forum(gid, GAMES[gid], cookie_str)
        except Exception as e:
            r = {"line": f"{GAMES[gid]}: 请求异常 - {e}", "ok": False}
        lines.append(r["line"])
        print(r["line"])
        all_ok = all_ok and r["ok"]
        if i < len(gids) - 1:
            time.sleep(random.uniform(2, 5))
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
