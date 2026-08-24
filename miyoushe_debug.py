#!/usr/bin/env python3
"""米游社 Cookie 诊断工具（本地运行，值自动脱敏）

用法：
    MIYOUSHE_COOKIE='粘贴你的完整Cookie' python3 miyoushe_debug.py [gid]

会依次用多种 Cookie 字段组合与 DS 签名变体请求米游社接口，
根据哪个组合能通过认证来定位问题。
"""

import hashlib
import json
import os
import random
import string
import sys
import time

import requests

K2_NEW = "QVu5OdwEWxkq9ygpYBgDprR5tI471HWQ"   # 2.81.1
K2_OLD = "JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS"   # 2.104.0 (trss-plugin)

USER_URL = "https://bbs-api.miyoushe.com/user/api/getUserFullInfo"
STATUS_URL = "https://bbs-api.miyoushe.com/apihub/sapi/querySignInStatus"
CTOKEN_URL = "https://passport-api.mihoyo.com/account/auth/api/getCookieAccountInfoBySToken"


def rs(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def ds1(salt):
    t = int(time.time())
    r = rs(6)
    return f"{t},{r},{md5(f'salt={salt}&t={t}&r={r}')}"


def ds2(body="", query="", salt=K2_NEW):
    t = int(time.time())
    r = random.randint(100001, 199999)
    return f"{t},{r},{md5(f'salt={salt}&t={t}&r={r}&b={body}&q={query}')}"


def mask(v):
    if not v:
        return "(空)"
    return v[:8] + f"...({len(v)}位)"


def parse(cookie_str):
    out = {}
    for item in cookie_str.replace("\n", "").split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def headers_for(ver, ua, cookie_str, salt):
    return {
        "User-Agent": ua,
        "Referer": "https://app.mihoyo.com",
        "x-rpc-app_version": ver,
        "x-rpc-app_id": "bll8iq97cem8",
        "x-rpc-verify_key": "bll8iq97cem8",
        "x-rpc-client_type": "2",
        "x-rpc-device_id": rs(16),
        "x-rpc-device_name": rs(16),
        "x-rpc-device_model": rs(16),
        "x-rpc-sys_version": "12",
        "x-rpc-channel": "mihoyo",
        "DS": ds1(salt),
        "Cookie": cookie_str,
    }


def main():
    raw = os.environ.get("MIYOUSHE_COOKIE", "").strip()
    if not raw:
        print("用法: MIYOUSHE_COOKIE='<Cookie>' python3 miyoushe_debug.py")
        sys.exit(1)
    gid = sys.argv[1] if len(sys.argv) > 1 else "6"

    c = parse(raw)
    print("== Cookie 字段解析 ==")
    for k, v in c.items():
        print(f"  {k} = {mask(v)}")

    uid = c.get("stuid") or c.get("ltuid") or ""
    mid = c.get("mid", "")
    stoken = c.get("stoken", "")

    variants = [
        ("完整Cookie原样", raw),
        ("stoken+mid(官方推荐)", f"stoken={stoken};mid={mid}"),
        ("stoken+stuid+mid", f"stoken={stoken};stuid={uid};mid={mid}"),
    ]
    combos = [
        ("v2.81.1 新盐", "2.81.1",
         "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36 miHoYoBBS/2.81.1",
         K2_NEW),
        ("v2.104.0 旧盐(trss)", "2.104.0",
         "Hyperion/550 CFNetwork/3860.500.112 Darwin/25.4.0",
         K2_OLD),
    ]

    print("\n== 认证探测（getUserFullInfo，-100=认证失败，0=成功）==")
    working = []
    for vname, cookie_str in variants:
        for cname, ver, ua, salt in combos:
            try:
                r = requests.get(
                    USER_URL, params={"uid": uid},
                    headers=headers_for(ver, ua, cookie_str, salt), timeout=15)
                d = r.json()
                rc, msg = d.get("retcode"), d.get("message", "")
            except Exception as e:
                rc, msg = "ERR", str(e)[:40]
            mark = ""
            if rc == 0:
                mark = "  ✅✅✅"
                working.append((vname, cname))
            print(f"  [{cname}] {vname}: retcode={rc} {msg}{mark}")

    if working:
        print(f"\n可用组合: {working}")
        print("\n== 用首个可用组合测签到状态接口 ==")
        vname, cname = working[0]
        idx = [v[0] for v in variants].index(vname)
        ci = [x[0] for x in combos].index(cname)
        _, ver, ua, salt = combos[ci]
        r = requests.get(STATUS_URL, params={"gids": gid},
                         headers=headers_for(ver, ua, variants[idx][1], salt), timeout=15)
        print(f"  querySignInStatus(gids={gid}): {json.dumps(r.json(), ensure_ascii=False)}")

        # 状态接口失败时，追加测试其他认证方式与直接签到
        status_rc = r.json().get("retcode")
        cookie_token = c.get("cookie_token", "")

        if status_rc != 0 and cookie_token:
            print("\n== 状态接口 - 用 cookie_token 认证重试 ==")
            ct_cookie = f"account_id={uid};cookie_token={cookie_token}"
            h = headers_for(ver, ua, ct_cookie, salt)
            r2 = requests.get(STATUS_URL, params={"gids": gid}, headers=h, timeout=15)
            print(f"  querySignInStatus(ctoken): {json.dumps(r2.json(), ensure_ascii=False)}")

        print("\n== 直接实测签到接口 signIn（DS2 签名）==")
        body = json.dumps({"gids": gid}, separators=(",", ":"))
        for vname2, cookie_str in variants[:3]:
            h = headers_for("2.81.1",
                            "Mozilla/5.0 (Linux; Android 13) miHoYoBBS/2.81.1",
                            cookie_str, K2_NEW)
            h["DS"] = ds2(body)
            try:
                r3 = requests.post(
                    "https://bbs-api.miyoushe.com/apihub/app/api/signIn",
                    data=body, headers=h, timeout=15)
                d3 = r3.json()
                print(f"  signIn[{vname2}]: retcode={d3.get('retcode')} {d3.get('message','')}"
                      + (f" points={d3['data'].get('points')}" if isinstance(d3.get('data'), dict) else ""))
            except Exception as e:
                print(f"  signIn[{vname2}]: ERR {str(e)[:60]}")
    else:
        print("\n❌ 所有组合均认证失败 —— Cookie 本身无效或已过期")
        print("   排查建议：")
        print("   1. 确认 Secret 值是整行 Cookie，无换行、无多余文字")
        print("   2. 重新扫码生成一次，立即测试（stoken 不应秒失效）")
        print("   3. 若网页获取的失败，改用本地脚本对比: python miyoushe_qr_login.py")

    # stoken 本体有效性独立验证（走 passport-api，不依赖 bbs 头）
    print("\n== stoken 有效性独立验证（passport-api）==")
    r = requests.get(
        CTOKEN_URL,
        params={"stoken": stoken, "uid": uid, "mid": mid},
        headers={"User-Agent": "HYPContainer/1.3.3.182",
                 "x-rpc-app_id": "ddxf5dufpuyo", "x-rpc-client_type": "3"},
        timeout=15,
    )
    d = r.json()
    ok = d.get("retcode") == 0
    print(f"  getCookieAccountInfoBySToken: retcode={d.get('retcode')} {d.get('message','')}"
          + ("  ✅ stoken 有效！" if ok else ""))
    if ok:
        print("  → 结论：stoken 有效，问题在 bbs-api 的请求头/签名组合")


if __name__ == "__main__":
    main()
