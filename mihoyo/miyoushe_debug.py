#!/usr/bin/env python3
"""米游社 Cookie 诊断工具（本地运行，值自动脱敏）

用法：
    bash run.sh 的环境导入后直接运行：
        python3 mihoyo/miyoushe_debug.py [游戏序号]
    或手动传 Cookie：
        MIYOUSHE_COOKIE='粘贴你的完整Cookie' python3 mihoyo/miyoushe_debug.py

检测项（全部只读，不会实际签到）：
1. Cookie 字段解析
2. stoken 有效性（passport-api，独立于任何签名逻辑；网页版 Cookie 无 stoken 时跳过）
3. 游戏角色绑定与每日签到状态（luna 正式链路）
"""

import os
import sys

import requests

from miyoushe_sign import (
    GAMES, BINDING_URL,
    web_headers, gen_ds, parse_cookie,
    build_web_cookie, set_device,
)


def mask(v):
    if not v:
        return "(空)"
    return v[:8] + f"...({len(v)}位)"


def load_cookie_from_api_file():
    """环境变量缺失时，从项目根目录 api.txt 读取（逐行解析，容忍值内分号）"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api.txt")
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "MIYOUSHE_COOKIE":
                return v.strip().strip("'\"")
    except OSError:
        pass
    return ""


def main():
    raw = os.environ.get("MIYOUSHE_COOKIE", "").strip()
    if not raw:
        raw = load_cookie_from_api_file()
    if not raw:
        print("用法: MIYOUSHE_COOKIE='<Cookie>' python3 mihoyo/miyoushe_debug.py [序号]")
        print("（或先在 api.txt 中配置 MIYOUSHE_COOKIE）")
        sys.exit(1)
    only = sys.argv[1] if len(sys.argv) > 1 else None

    c = parse_cookie(raw)
    print("== Cookie 字段解析 ==")
    for k, v in c.items():
        print(f"  {k} = {mask(v)}")

    # 1. 准备可用的网页 Cookie
    print("\n== 1. 登录态验证 ==")
    try:
        set_device(c.get("device_id"))
        web_cookie = build_web_cookie(c)
        fmt = ("v1(cookie_token)" if c.get("cookie_token")
               else "v2(cookie_token_v2)" if c.get("cookie_token_v2")
               else "stoken 换取")
        print(f"  ✅ 凭证格式: {fmt}")
    except Exception as e:
        print(f"  ❌ {str(e)[:60]}")
        sys.exit(1)

    # 2. 角色绑定
    print("\n== 2. 游戏角色绑定 ==")
    roles = []
    for biz in sorted({g["biz"] for g in GAMES}):
        try:
            rr = requests.get(BINDING_URL, params={"game_biz": biz},
                              headers=web_headers(web_cookie), timeout=15)
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

    # 3. 各游戏签到状态（luna 正式链路，只读）
    print("\n== 3. 游戏签到状态（只读查询，不会实际签到）==")
    targets = [g for g in GAMES if not only or g["biz"] == only]
    for g in targets:
        role = next((r_ for r_ in roles if r_.get("game_biz") == g["biz"]), None)
        if not role:
            print(f"  {g['name']}: 账号未绑定此游戏，跳过")
            continue
        url = f"{g['base']}/event/luna{g['sub']}/info"
        h = web_headers(web_cookie)
        if g["signgame"]:
            h["x-rpc-signgame"] = g["signgame"]
        h["DS"] = gen_ds()
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
