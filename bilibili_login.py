#!/usr/bin/env python3
"""Bilibili 每日登录脚本 - 通过 GitHub Actions 自动登录领取硬币"""

import os
import sys
import requests
from datetime import datetime

from notify import send_notification

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
    print(f"[B站登录] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not SESSDATA or not DEDEUSERID:
        print("错误: 未设置 BILI_SESSDATA / BILI_DEDEUSERID")
        sys.exit(1)

    result = daily_login()

    if result.get("error"):
        msg = f"登录失败: {result['error']} (code={result['code']})"
        print(msg)
        send_notification("B站登录失败", msg)
        sys.exit(1)

    if result["success"]:
        lines = [
            f"用户: {result['uname']}",
            f"硬币: {result['money']}",
            f"等级: LV{result['level']}",
            f"大会员: {'是' if result['vip_status'] else '否'}",
            "每日硬币已领取",
        ]
        report = "\n".join(lines)
        print(report)
        send_notification("B站每日登录", report)
    else:
        msg = "登录失败: Cookie 可能已过期，请重新获取"
        print(msg)
        send_notification("B站登录失败", msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
