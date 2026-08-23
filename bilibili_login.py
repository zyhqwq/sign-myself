#!/usr/bin/env python3
"""Bilibili 每日登录脚本 - 支持多账号"""

import os
import sys
import requests
from datetime import datetime

from notify import send_notification, print_notify_results

NAV_URL = "https://api.bilibili.com/x/web-interface/nav"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}


def daily_login(sessdata, jct, dedeuserid) -> dict:
    cookies = {
        "SESSDATA": sessdata,
        "bili_jct": jct,
        "DedeUserID": dedeuserid,
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

    raw_sessdata = os.environ.get('BILI_SESSDATA', '')
    raw_jct = os.environ.get('BILI_JCT', '')
    raw_dedeuserid = os.environ.get('BILI_DEDEUSERID', '')

    if not raw_sessdata or not raw_dedeuserid:
        msg = "错误: 未设置 BILI_SESSDATA / BILI_DEDEUSERID"
        print(msg)
        print_notify_results(send_notification("B站登录失败", msg))
        sys.exit(1)

    sessdata_list = [s.strip() for s in raw_sessdata.split(',') if s.strip()]
    jct_list = [s.strip() for s in raw_jct.split(',') if s.strip()]
    dedeuserid_list = [s.strip() for s in raw_dedeuserid.split(',') if s.strip()]

    if len(sessdata_list) != len(dedeuserid_list):
        msg = f"错误: BILI_SESSDATA ({len(sessdata_list)}个) 与 BILI_DEDEUSERID ({len(dedeuserid_list)}个) 数量不匹配"
        print(msg)
        print_notify_results(send_notification("B站登录失败", msg))
        sys.exit(1)

    while len(jct_list) < len(sessdata_list):
        jct_list.append('')

    accounts = list(zip(sessdata_list, jct_list, dedeuserid_list))
    print(f"共 {len(accounts)} 个账号")

    results = []
    all_ok = True

    for i, (sessdata, jct, dedeuserid) in enumerate(accounts):
        label = f"账号{i + 1}"
        print(f"\n--- {label} ---")

        result = daily_login(sessdata, jct, dedeuserid)

        if result.get("error"):
            line = f"{label}: 登录失败 - {result['error']} (code={result['code']})"
            all_ok = False
        elif result["success"]:
            line = (
                f"{label} [{result['uname']}]: "
                f"硬币 {result['money']}, LV{result['level']}, "
                f"大会员{'是' if result['vip_status'] else '否'}"
            )
        else:
            line = f"{label}: Cookie 已过期"
            all_ok = False

        print(line)
        results.append(line)

    report = "\n".join(results)
    title = "B站每日登录" if all_ok else "B站登录部分失败"
    print(f"\n{report}")
    print_notify_results(send_notification(title, report))

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
