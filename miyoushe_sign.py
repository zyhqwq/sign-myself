#!/usr/bin/env python3
"""米游社游戏签到脚本 - GitHub Actions 专用版

使用 MIYOUSHE_COOKIE（由本地 miyoushe_qr_login.py 扫码获取）完成
原神 / 崩坏:星穹铁道 / 绝区零 的每月签到福利（领原石、燃料等）。

特性：
- 自动用 Cookie 内的 stoken 刷新 cookie_token（stoken 长期有效，一次扫码长期免维护）
- 自动检测账号绑定的游戏角色，只签有角色的游戏
- 社区签到（米游币）接口已被米哈游封禁第三方调用，本脚本不做社区签到

参考实现：
- TimeRainStarSky/TRSS-Plugin 扫码登录流程
- Womsxd/MihoyoBBSTools 游戏签到接口与请求头
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

from notify import send_notification, print_notify_results, format_sign_entry

# ================== 接口地址 ==================
PASSPORT_API = "https://passport-api.mihoyo.com"
TAKUMI_API = "https://api-takumi.mihoyo.com"
NAP_API = "https://act-nap-api.mihoyo.com"
BINDING_URL = f"{TAKUMI_API}/binding/api/getUserGameRolesByCookie"

# 支持的游戏（act_id 参考 MihoyoBBSTools 与 astrbot_plugin_miyoqian）
GAMES = [
    {"biz": "hk4e_cn", "name": "原神", "act_id": "e202311201442471",
     "signgame": "hk4e", "base": TAKUMI_API, "sub": ""},
    {"biz": "hkrpg_cn", "name": "崩坏:星穹铁道", "act_id": "e202304121516551",
     "signgame": "", "base": TAKUMI_API, "sub": ""},
    {"biz": "nap_cn", "name": "绝区零", "act_id": "e202406242138391",
     "signgame": "zzz", "base": NAP_API, "sub": "/zzz"},
]

COOKIE_ENV = "MIYOUSHE_COOKIE"

# 网页端 DS 盐值（2026 新版，参考 astrbot_plugin_miyoqian）
DS_SALT_WEB = "G1ktdwFL4IyGkHuuWSmz0wUe9Db9scyK"

# 登录失效相关返回码
LOGIN_INVALID = (-100, -101, 10001, 1008, 10103, 10104)
ALREADY_SIGNED = -5003
CAPTCHA = 1034


def random_string(n):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def gen_ds():
    """DS1 签名（网页端盐值）"""
    t = str(int(time.time()))
    r = random_string(6)
    c = hashlib.md5(f"salt={DS_SALT_WEB}&t={t}&r={r}".encode()).hexdigest()
    return f"{t},{r},{c}"


def passport_headers(device_id=None):
    return {
        "User-Agent": "HYPContainer/1.3.3.182",
        "x-rpc-app_id": "ddxf5dufpuyo",
        "x-rpc-client_type": "3",
        "x-rpc-device_id": device_id or random_string(16),
    }


def web_headers(cookie_str):
    """游戏签到请求头（对齐 astrbot_plugin_miyoqian 验证可用的组合）"""
    return {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 12; Unspecified Device) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.129 Mobile "
            "Safari/537.36 miHoYoBBS/2.109.0"
        ),
        "x-rpc-app_version": "2.109.0",
        "x-rpc-client_type": "5",
        "Origin": "https://act.mihoyo.com",
        "Referer": "https://act.mihoyo.com/",
        "x-rpc-channel": "miyousheluodi",
        "X-Requested-With": "com.mihoyo.hyperion",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,en-US;q=0.8",
        "Connection": "keep-alive",
        "x-rpc-device_id": random_string(32),
        "Cookie": cookie_str,
    }


def parse_cookie(cookie_str):
    cookies = {}
    for item in cookie_str.replace("\n", "").split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def refresh_cookie_token(cookies):
    """用 stoken 刷新 cookie_token（stoken 长期有效，实现免维护续期）"""
    stoken = cookies.get("stoken")
    uid = cookies.get("stuid") or cookies.get("ltuid") or ""
    mid = cookies.get("mid", "")
    if not stoken:
        raise Exception("Cookie 缺少 stoken 字段")

    resp = requests.get(
        f"{PASSPORT_API}/account/auth/api/getCookieAccountInfoBySToken",
        params={"stoken": stoken, "uid": uid, "mid": mid},
        headers={**passport_headers(), "Cookie": f"stoken={stoken};stuid={uid};mid={mid}"},
        timeout=15,
    )
    data = resp.json()
    if data.get("retcode") != 0:
        raise Exception(f"stoken 已失效({data.get('message')})，请重新扫码获取")

    token = data["data"].get("cookie_token")
    if not token:
        raise Exception("刷新 cookie_token 失败：返回为空")

    # 回写，保证本次运行内后续请求一致
    cookies["cookie_token"] = token
    return f"account_id={uid};cookie_token={token}"


def get_roles(cookie_str):
    """获取账号绑定的全部游戏角色"""
    roles = []
    for biz in sorted({g["biz"] for g in GAMES}):
        try:
            resp = requests.get(
                BINDING_URL,
                params={"game_biz": biz},
                headers=web_headers(cookie_str),
                timeout=15,
            )
            data = resp.json()
            if data.get("retcode") == 0:
                for role in data.get("data", {}).get("list", []):
                    roles.append(role)
        except Exception:
            pass
    return roles


def luna_request(method, path, game, cookie_str, **params):
    url = f"{game['base']}/event/luna{game['sub']}/{path}"
    headers = web_headers(cookie_str)
    if game["signgame"]:
        headers["x-rpc-signgame"] = game["signgame"]
    headers["DS"] = gen_ds()
    payload = {"lang": "zh-cn", "act_id": game["act_id"]}
    payload.update(params)
    if method == "get":
        resp = requests.get(url, params=payload, headers=headers, timeout=15)
    else:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
    return resp.json()


def get_awards(game, cookie_str):
    """获取签到活动奖励列表（用于展示每日获得的道具）"""
    url = f"{game['base']}/event/luna{game['sub']}/home"
    headers = web_headers(cookie_str)
    if game["signgame"]:
        headers["x-rpc-signgame"] = game["signgame"]
    headers["DS"] = gen_ds()
    try:
        resp = requests.get(url, params={"lang": "zh-cn", "act_id": game["act_id"]},
                            headers=headers, timeout=15)
        data = resp.json()
        if data.get("retcode") == 0:
            return data.get("data", {}).get("awards") or []
    except Exception:
        pass
    return []


def award_of(awards, day_1based):
    """按第几天（1-based）取奖励描述"""
    if awards and 1 <= day_1based <= len(awards):
        a = awards[day_1based - 1]
        return f"「{a.get('name')}」x{a.get('cnt', 1)}"
    return ""


def sign_game(game, role, cookie_str, account_label):
    name = game["name"]
    role_label = f"{role['nickname']} Lv{role['level']}"
    uid, region = str(role["game_uid"]), role["region"]

    try:
        info = luna_request("get", "info", game, cookie_str, uid=uid, region=region)
    except Exception as e:
        return {"line": format_sign_entry(name, account_label, role_label, f"请求异常 - {str(e)[:60]}"), "ok": False}

    retcode = info.get("retcode")
    if retcode in LOGIN_INVALID:
        return {"line": format_sign_entry(name, account_label, role_label, "Cookie 已失效，请重新扫码获取"), "ok": False}
    if retcode == CAPTCHA:
        return {"line": format_sign_entry(name, account_label, role_label, "触发风控验证(1034)，今日未能签到"), "ok": False}
    if retcode != 0:
        return {"line": format_sign_entry(name, account_label, role_label, f"查询签到状态失败 - {info.get('message')} ({retcode})"), "ok": False}

    data = info.get("data", {})
    if data.get("first_bind"):
        return {"line": format_sign_entry(name, account_label, role_label, "首次绑定，请先在米游社 App 手动签到一次"), "ok": False}

    total_days = int(data.get("total_sign_day") or 0)
    is_sign = data.get("is_sign")
    if isinstance(is_sign, str):
        is_sign = is_sign.strip().lower() in ("true", "1")
    if is_sign:
        award_str = award_of(get_awards(game, cookie_str), total_days)
        award_text = f"，今日奖励:{award_str}" if award_str else ""
        return {"line": format_sign_entry(name, account_label, role_label,
                                          f"今天已签到{award_text}（累计{total_days}天）"), "ok": True}

    result = luna_request("post", "sign", game, cookie_str, uid=uid, region=region)
    rc2 = result.get("retcode")

    if rc2 == 0:
        sign_data = result.get("data") or {}
        award = sign_data.get("award") or {}
        award_str = f"，获得「{award.get('name')}」x{award.get('cnt')}" if award.get("name") else ""
        return {"line": format_sign_entry(name, account_label, role_label, f"签到成功{award_str}（累计{total_days + 1}天）"), "ok": True}
    if rc2 == ALREADY_SIGNED:
        return {"line": f"{name}: 今天已签到（累计{total_days}天）", "ok": True}
    if rc2 == CAPTCHA:
        return {"line": f"{name}: 触发风控验证(1034)，今日未能签到（可明天再试）", "ok": False}
    if rc2 in LOGIN_INVALID:
        return {"line": format_sign_entry(name, account_label, role_label, "Cookie 已失效，请重新扫码获取"), "ok": False}

    msg = result.get("message", "")
    return {"line": format_sign_entry(name, account_label, role_label, f"签到失败 - {msg} (retcode={rc2})"), "ok": False}


def process_account(idx, cookie_str):
    cookies = parse_cookie(cookie_str)

    # 1. 续期 cookie_token
    try:
        cookie_str = refresh_cookie_token(cookies)
    except Exception as e:
        return [f"账号_{idx}: {e}"], False

    # 2. 获取角色
    try:
        roles = get_roles(cookie_str)
    except Exception as e:
        return [f"账号_{idx}: 获取角色失败 - {str(e)[:60]}"], False

    if not roles:
        return [f"账号_{idx}: 未绑定任何游戏角色，无需签到"], True

    # 可选：只签指定游戏（MIYOUSHE_ONLY=biz1,biz2）
    only = {b.strip() for b in os.environ.get("MIYOUSHE_ONLY", "").split(",") if b.strip()}
    if only:
        roles = [r for r in roles if r.get("game_biz") in only]
        if not roles:
            return ["所选游戏未绑定角色，跳过"], True

    print(f"昵称绑定角色数: {len(roles)}")

    lines, all_ok = [], True
    account_label = f"账号{idx}"
    for i, role in enumerate(roles):
        game = next((g for g in GAMES if g["biz"] == role.get("game_biz")), None)
        if not game:
            continue
        try:
            r = sign_game(game, role, cookie_str, account_label)
        except Exception as e:
            r = {"line": format_sign_entry(game["name"], account_label,
                                           f"{role['nickname']} Lv{role['level']}",
                                           f"请求异常 - {str(e)[:60]}"), "ok": False}
        lines.append(r["line"])
        all_ok = all_ok and r["ok"]
        if i < len(roles) - 1:
            time.sleep(random.uniform(2, 5))
    return lines, all_ok


def main():
    print(f"[米游社游戏签到] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    raw = os.environ.get(COOKIE_ENV, "").strip()
    if not raw:
        msg = f"错误: 未设置 {COOKIE_ENV}（请在本地运行 miyoushe_qr_login.py 扫码获取）"
        print(msg)
        print_notify_results(send_notification("米游社游戏签到失败", msg))
        sys.exit(1)

    account_list = [c.strip() for c in raw.split(",") if c.strip()]
    print(f"共 {len(account_list)} 个账号")

    results, all_ok = [], True
    for idx, cookie_str in enumerate(account_list, 1):
        print(f"\n--- 账号{idx} ---")
        lines, ok = process_account(idx, cookie_str)
        results.extend(lines)
        all_ok = all_ok and ok

    report = "\n\n".join(results)
    title = "米游社游戏签到成功" if all_ok else "米游社游戏签到部分失败"
    print(f"\n{report}")
    print_notify_results(send_notification(title, report))

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
