#!/usr/bin/env python3
"""米游社 Cookie 诊断工具（本地运行，值自动脱敏）

用法：
    MIYOUSHE_COOKIE='粘贴你的完整Cookie' python3 mihoyo/miyoushe_debug.py [游戏序号]

检测项：
1. Cookie 字段解析
2. stoken 有效性（passport-api，独立于任何签名逻辑）
3. 米游社用户信息接口认证
4. 游戏角色绑定与每日签到状态（luna 接口，当前使用的正式链路，只读不签到）
"""

import json
import os
import sys

import requests

from miyoushe_sign import (
    GAMES, USER_INFO_URL, BINDING_URL,
    bbs_headers, ds1, ds2, parse_cookie,
)


def mask(v):
    if not v:
        return "(空)"
    return v[:8] + f"...({len(v)}位)"


def main():
    raw = os.environ.get("MIYOUSHE_COOKIE", "").strip()
    if not raw:
        print("用法: MIYOUSHE_COOKIE='<Cookie>' python3 mihoyo/miyoushe_debug.py [序号]")
        sys.exit(1)
    only = sys.argv[1] if len(sys.argv) > 1 else None

    c = parse_cookie(raw)
    uid = c.get("stuid") or c.get("ltuid") or ""
    mid = c.get("mid", "")
    stoken = c.get("stoken", "")
    print("== Cookie 字段解析 ==")
    for k, v in c.items():
        print(f"  {k} = {mask(v)}")

    # 1. stoken 独立验证（passport-api）
    print("\n== 1. stoken 独立验证 ==")
    r = requests.get(
        "https://passport-api.mihoyo.com/account/auth/api/getCookieAccountInfoBySToken",
        params={"stoken": stoken, "uid": uid, "mid": mid},
        headers={"User-Agent": "HYPContainer/1.3.3.182",
                 "x-rpc-app_id": "ddxf5dufpuyo", "x-rpc-client_type": "3",
                 "Cookie": f"stoken={stoken};stuid={uid};mid={mid}"},
        timeout=15)
    d = r.json()
    ok = d.get("retcode") == 0
    print(f"  retcode={d.get('retcode')} {d.get('message','')}"
          + ("   ✅ stoken 有效" if ok else "   ❌ Cookie 已失效，请重新扫码"))
    if not ok:
        sys.exit(1)

    ct = d["data"].get("cookie_token")
    print(f"  新 cookie_token: {mask(ct)}")
    web_cookie = f"account_id={uid};cookie_token={ct}"

    # 2. 米游社用户信息认证
    print("\n== 2. 米游社用户信息接口 ==")
    h = bbs_headers(f"stoken={stoken};stuid={uid};mid={mid}")
    h["DS"] = ds1()
    r = requests.get(USER_INFO_URL, params={"uid": uid}, headers=h, timeout=15)
    d = r.json()
    if d.get("retcode") == 0:
        nick = d["data"]["user_info"].get("nickname", "")
        print(f"  retcode=0   ✅ 昵称: {nick}")
    else:
        print(f"  retcode={d.get('retcode')} {d.get('message','')}")
    web_cookie = f"account_id={uid};cookie_token={ct}"

    # 3. 角色绑定
    print("\n== 3. 游戏角色绑定 ==")
    roles = []
    for biz in sorted({g["biz"] for g in GAMES}):
        try:
            rr = requests.get(BINDING_URL, params={"game_biz": biz},
                              headers=bbs_headers(web_cookie), timeout=15)
            dd = rr.json()
            if dd.get("retcode") == 0:
                lst = dd.get("data", {}).get("list", [])
                for role in lst:
                    roles.append(role)
                    print(f"  {biz}: {role.get('nickname')} Lv{role.get('level')} "
                          f"region={role.get('region')}")
                if not lst:
                    print(f"  {biz}: 无绑定角色")
            else:
                print(f"  {biz}: 查询失败 ({dd.get('message','')[:30]})")
        except Exception as e:
            print(f"  {biz}: ERR {str(e)[:40]}")

    if not roles:
        print("\n未查到任何游戏角色，无法进行游戏签到")
        return

    # 4. 各游戏签到状态（luna 正式链路，只读）
    print("\n== 4. 游戏签到状态（只读查询，不会实际签到）==")
    targets = [g for g in GAMES if not only or g["biz"] == only]
    for g in targets:
        role = next((r_ for r_ in roles if r_.get("game_biz") == g["biz"]), None)
        if not role:
            print(f"  {g['name']}: 账号未绑定此游戏，跳过")
            continue
        url = f"{g['base']}/event/luna{g['sub']}/info"
        h = bbs_headers(web_cookie)
        if g["signgame"]:
            h["x-rpc-signgame"] = g["signgame"]
        h["DS"] = ds2()
        try:
            rr = requests.get(url, params={"lang": "zh-cn", "act_id": g["act_id"],
                                           "uid": str(role["game_uid"]),
                                           "region": role["region"]},
                              headers=h, timeout=15)
            dd = rr.json()
            if dd.get("retcode") == 0:
                data = dd["data"]
                state = "今日已签" if data.get("is_sign") else "今日未签"
                print(f"  {g['name']}: ✅ {state}（本月累计{data.get('total_sign_day')}天）")
            else:
                print(f"  {g['name']}: ❌ retcode={dd.get('retcode')} "
                      f"{str(dd.get('message',''))[:50]}")
        except Exception as e:
            print(f"  {g['name']}: ERR {str(e)[:50]}")


if __name__ == "__main__":
    main()
