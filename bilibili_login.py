#!/usr/bin/env python3
"""Bilibili 每日登录脚本 - 通过 GitHub Actions 自动登录领取硬币"""

import json
import os
import sys
import requests

# ================== 配置 ==================
SESSDATA = os.environ.get('BILI_SESSDATA', '')
BILI_JCT = os.environ.get('BILI_JCT', '')
DEDEUSERID = os.environ.get('BILI_DEDEUSERID', '')

NAV_URL = "https://api.bilibili.com/x/web-interface/nav"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}


def daily_login() -> dict:
    cookies = {
        "SESSDATA": SESSDATA,
        "bili_jct": BILI_JCT,
        "DedeUserID": DEDEUSERID,
    }

    resp = requests.get(NAV_URL, headers=HEADERS, cookies=cookies, timeout=15)
    data = resp.json()

    if data["code"] == 0:
        info = data["data"]
        return {
            "success": info.get("isLogin", False),
            "uname": info.get("uname", "unknown"),
            "money": info.get("money", "?"),
            "vip_status": info.get("vipStatus", 0),
            "level": info.get("level_info", {}).get("current_level", "?"),
        }
    else:
        return {
            "success": False,
            "error": data.get("message", "unknown error"),
            "code": data["code"],
        }


def main():
    print("=" * 40)
    print("Bilibili 每日登录")
    print("=" * 40)

    if not SESSDATA or not DEDEUSERID:
        print("错误: 请在 GitHub Secrets 中设置 BILI_SESSDATA 和 BILI_DEDEUSERID")
        sys.exit(1)

    result = daily_login()

    if result.get("error"):
        print(f"登录失败: {result['error']} (code={result['code']})")
        sys.exit(1)

    if result["success"]:
        print(f"用户: {result['uname']}")
        print(f"硬币: {result['money']}")
        print(f"等级: LV{result['level']}")
        print(f"大会员: {'是' if result['vip_status'] else '否'}")
        print("登录成功，每日硬币已领取")
    else:
        print("登录失败: Cookie 可能已过期，请重新获取")
        sys.exit(1)


if __name__ == "__main__":
    main()
