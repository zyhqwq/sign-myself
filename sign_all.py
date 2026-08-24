#!/usr/bin/env python3
"""每日签到统一入口 - 按序号选择要运行的游戏

序号对应（通过 Secret `SIGN_GAMES` 配置，英文逗号分隔，默认全部）：
    1 = 明日方舟   (森空岛, SKLAND_TOKEN)
    2 = 终末地     (森空岛, SKLAND_TOKEN)
    3 = 原神       (米游社, MIYOUSHE_COOKIE)
    4 = 崩坏:星穹铁道 (米游社, MIYOUSHE_COOKIE)
    5 = 绝区零     (米游社, MIYOUSHE_COOKIE)

通知按平台聚合为一条汇总消息发送；任一任务失败则整体退出码为 1。
"""

import os
import subprocess
import sys
import tempfile

import notify

# 任务定义: 序号 -> (名称, 脚本, 平台, 额外环境变量)
JOBS = {
    "1": {"name": "明日方舟", "platform": "森空岛签到",
          "script": "skland/arknight_github.py", "env": None},
    "2": {"name": "终末地", "platform": "森空岛签到",
          "script": "skland/endfield_github.py", "env": None},
    "3": {"name": "原神", "platform": "米游社签到",
          "script": "mihoyo/miyoushe_sign.py",
          "env": {"MIYOUSHE_ONLY": "hk4e_cn"}},
    "4": {"name": "崩坏:星穹铁道", "platform": "米游社签到",
          "script": "mihoyo/miyoushe_sign.py",
          "env": {"MIYOUSHE_ONLY": "hkrpg_cn"}},
    "5": {"name": "绝区零", "platform": "米游社签到",
          "script": "mihoyo/miyoushe_sign.py",
          "env": {"MIYOUSHE_ONLY": "nap_cn"}},
}

PLATFORM_ORDER = ["森空岛签到", "米游社签到"]


def read_reports(report_dir):
    """读取一个任务报告目录里的全部内容"""
    parts = []
    if not os.path.isdir(report_dir):
        return parts
    for fname in sorted(os.listdir(report_dir)):
        path = os.path.join(report_dir, fname)
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                parts.append(content)
        except Exception:
            pass
    return parts


def main():
    # GitHub Secrets 未配置时变量为空字符串，需视为未设置
    raw = os.environ.get("SIGN_GAMES", "").strip() or "1,2,3,4,5"
    selected = {s.strip() for s in raw.split(",") if s.strip() in JOBS}

    if not selected:
        print(f"错误: SIGN_GAMES='{raw}' 中没有有效的序号（可选 1-5）")
        sys.exit(1)

    print(f"[每日签到] 选择的游戏: {', '.join(sorted(selected))}")

    failed = []
    # platform -> list of (任务名, 报告列表)，保持运行顺序
    platform_reports = {p: [] for p in PLATFORM_ORDER}

    for key in ("1", "2", "3", "4", "5"):
        if key not in selected:
            continue
        job = JOBS[key]
        name = job["name"]

        print(f"\n{'=' * 20} {name} {'=' * 20}")

        # 每个任务独立报告目录
        report_dir = tempfile.mkdtemp(prefix=f"sign_{key}_")
        env = dict(os.environ)
        env["SIGN_REPORT_DIR"] = report_dir
        env.update(job["env"] or {})

        rc = subprocess.run([sys.executable, job["script"]], env=env).returncode
        if rc != 0:
            failed.append(name)

        reports = read_reports(report_dir)
        if reports:
            platform_reports[job["platform"]].append((name, "\n".join(reports)))
        else:
            platform_reports[job["platform"]].append(
                (name, "(未捕获到报告)" if rc == 0 else "运行失败，详见 Actions 日志"))

    # 组装按平台分组的汇总消息
    sections = []
    for platform in PLATFORM_ORDER:
        entries = platform_reports[platform]
        if not entries:
            continue
        block = [f"【{platform}】"]
        for _, content in entries:
            block.append(content)
        sections.append("\n\n".join(block))

    if sections:
        overall_ok = not failed
        title = "每日签到汇总 - 全部成功" if overall_ok else "每日签到汇总 - 部分失败"
        body = "\n\n".join(sections)
        if failed:
            body += f"\n\n 失败的任务: {', '.join(failed)}"
        print("\n 发送聚合通知...")
        results = notify.send_notification(title, body)
        notify.print_notify_results(results)
    else:
        print("\n 未捕获到任何子任务报告，无法发送聚合通知")

    print(f"\n{'=' * 20} 汇总 {'=' * 20}")
    if failed:
        print(f"失败的任务: {', '.join(failed)}")
        sys.exit(1)
    print("全部成功")


if __name__ == "__main__":
    main()
