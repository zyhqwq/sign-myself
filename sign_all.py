#!/usr/bin/env python3
"""每日签到统一入口 - 按序号选择要运行的游戏

序号对应（通过 Secret `SIGN_GAMES` 配置，英文逗号分隔，默认全部）：
    1 = 明日方舟   (森空岛, SKLAND_TOKEN)
    2 = 终末地     (森空岛, SKLAND_TOKEN)
    3 = 原神       (米游社, MIYOUSHE_COOKIE)
    4 = 崩坏:星穹铁道 (米游社, MIYOUSHE_COOKIE)
    5 = 绝区零     (米游社, MIYOUSHE_COOKIE)

每个子任务独立发送通知，最后汇总结果；任一失败则整体退出码为 1。
"""

import os
import subprocess
import sys

NUMBER_MAP = {
    "1": ("明日方舟", "arknight_github.py", None),
    "2": ("终末地", "endfield_github.py", None),
    "3": ("原神", "miyoushe_sign.py", {"MIYOUSHE_ONLY": "hk4e_cn"}),
    "4": ("崩坏:星穹铁道", "miyoushe_sign.py", {"MIYOUSHE_ONLY": "hkrpg_cn"}),
    "5": ("绝区零", "miyoushe_sign.py", {"MIYOUSHE_ONLY": "nap_cn"}),
}


def main():
    # GitHub Secrets 未配置时变量为空字符串，需视为未设置
    raw = os.environ.get("SIGN_GAMES", "").strip() or "1,2,3,4,5"
    selected = {s.strip() for s in raw.split(",") if s.strip() in NUMBER_MAP}

    if not selected:
        print(f"错误: SIGN_GAMES='{raw}' 中没有有效的序号（可选 1-5）")
        sys.exit(1)

    print(f"[每日签到] 选择的游戏: {', '.join(sorted(selected))}")

    # 米游社的多个游戏合并成一次调用（共享一次 cookie_token 续期与角色查询）
    mys_bizs = sorted(NUMBER_MAP[k][2]["MIYOUSHE_ONLY"] for k in selected if k in ("3", "4", "5"))
    jobs = [(NUMBER_MAP[k][0], NUMBER_MAP[k][1], NUMBER_MAP[k][2]) for k in ("1", "2") if k in selected]
    if mys_bizs:
        jobs.append(("米游社游戏(" + ",".join(mys_bizs) + ")",
                     "miyoushe_sign.py", {"MIYOUSHE_ONLY": ",".join(mys_bizs)}))

    failed = []
    for name, script, extra_env in jobs:
        print(f"\n{'=' * 20} {name} {'=' * 20}")
        env = dict(os.environ)
        env.update(extra_env or {})
        rc = subprocess.run([sys.executable, script], env=env).returncode
        if rc != 0:
            failed.append(name)

    print(f"\n{'=' * 20} 汇总 {'=' * 20}")
    if failed:
        print(f"失败的任务: {', '.join(failed)}")
        sys.exit(1)
    print("全部成功")


if __name__ == "__main__":
    main()
