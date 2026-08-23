#!/usr/bin/env python3
"""测试所有已配置的通知渠道"""

import sys
from datetime import datetime

from notify import send_notification, get_webhook_status


def main():
    print(f"[通知测试] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)

    print("\n📋 当前配置状态：")
    for status in get_webhook_status():
        print(f"  {status}")

    print("\n📨 发送测试通知...")
    results = send_notification(
        "通知测试",
        f"这是一条测试消息\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n来源: GitHub Actions"
    )

    if not results:
        print("\n❌ 未配置任何通知渠道，请在 Secrets 中添加")
        sys.exit(1)

    print("\n📊 发送结果：")
    ok = 0
    fail = 0
    for name, result in results:
        icon = "✅" if result == "OK" else "❌"
        print(f"  {icon} {name}: {result}")
        if result == "OK":
            ok += 1
        else:
            fail += 1

    print(f"\n完成: {ok} 成功, {fail} 失败")
    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
