#!/usr/bin/env python3
"""米游社 / 森空岛 每日签到 一键配置向导

运行：python3 setup_sign.py
流程：环境检查 -> 收集凭证 -> 选择通知渠道 -> 测试运行 ->
      配置定时任务（北京时间，全部回车 = 每天 03:25）-> 完成

说明：
- 所有输入使用系统标准输入，删除键（Backspace/Delete）行为与终端一致，可正常修改
- 任何一步按 Ctrl+C 都会立即取消，未写入的配置不会保存
- 配置写入 api.txt；定时任务通过 crontab 安装，重复运行向导会覆盖旧的签到定时项
"""

import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
API_FILE = os.path.join(ROOT, "api.txt")

# ================== 通用输入工具 ==================

CANCEL_KEYS = ("q", "quit", "退出")


class Cancelled(Exception):
    """用户主动取消"""


def ask(prompt, default=None, validator=None, errmsg="输入不合法，请重新输入"):
    """标准输入提问。validator(v) 返回 True 表示合法；
    有 default 时直接回车取默认值；Ctrl+C / EOF 由上层捕获"""
    while True:
        suffix = f"（回车 = {default}）" if default is not None else ""
        try:
            v = input(f"{prompt}{suffix}: ").strip()
        except EOFError:
            raise Cancelled()
        if v == "" and default is not None:
            return default
        if validator is None or validator(v):
            return v
        print(f"  [!] {errmsg}")


def ask_yn(prompt, default_yes=True):
    while True:
        v = ask(f"{prompt} (y/n)", default="y" if default_yes else "n").lower()
        if v in ("y", "yes", "是"):
            return True
        if v in ("n", "no", "否"):
            return False
        print("  [!] 请输入 y 或 n")


def ask_url(prompt, prefix):
    def ok(u):
        return u.startswith(prefix)
    return ask(f"{prompt}\n  （需以 {prefix} 开头）", validator=ok,
               errmsg=f"地址必须以 {prefix} 开头")


# ================== 环境检查 ==================

def check_python():
    if sys.version_info < (3, 8):
        print(f"[X] 当前 Python 版本 {sys.version.split()[0]} 过低，需要 3.8 及以上")
        sys.exit(1)
    print(f"[OK] Python {sys.version.split()[0]}")


def check_deps():
    try:
        import requests  # noqa: F401
        import cryptography  # noqa: F401
        print("[OK] 依赖已安装")
        return
    except ImportError:
        print("[..] 缺少依赖，正在尝试自动安装 ...")

    req = os.path.join(ROOT, "requirements.txt")
    # 与 run.sh 相同的多级回退：覆盖 PEP 668（新版 Debian/Ubuntu）等限制
    if not subprocess.run([sys.executable, "-m", "pip", "--version"],
                          capture_output=True).returncode == 0:
        # pip 缺失：先试 ensurepip（无需 root），失败则需用户手动处理
        if subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"],
                          capture_output=True).returncode != 0:
            print("[X] 当前环境缺少 pip 且自动补齐失败。")
            print("    请用管理员权限执行: sudo apt-get install python3-pip")
            sys.exit(1)

    cmds = [
        [sys.executable, "-m", "pip", "install", "-r", req],
        [sys.executable, "-m", "pip", "install", "--user", "-r", req],
        [sys.executable, "-m", "pip", "install", "--break-system-packages",
         "--user", "-r", req],
    ]
    for cmd in cmds:
        if subprocess.run(cmd).returncode == 0:
            print("[OK] 依赖安装完成")
            return
    print("[X] 依赖安装失败，请手动执行:")
    print("    pip install --break-system-packages -r requirements.txt")
    sys.exit(1)


# ================== 凭证收集 ==================

def ask_nonempty(prompt):
    return ask(prompt, validator=lambda v: len(v) > 0, errmsg="不能为空")


COOKIE_ASK_ERRMSG = (
    "Cookie 格式不正确：应包含 account_id= / cookie_token= 或 stoken= 等字段，"
    "多个账号用英文逗号分隔")


def cookie_format_ok(v):
    """轻量校验：至少含一个凭证字段，避免明显粘错内容"""
    if "=" not in v:
        return False
    return any(k in v for k in ("account_id=", "cookie_token=", "stoken=", "ltoken="))


def read_api_file_values(keys):
    """从现有 api.txt 读取指定键（逐行解析，容忍值内分号与引号）"""
    vals = {}
    try:
        with open(API_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() in keys:
                    vals[k.strip()] = v.strip().strip("'\"")
    except OSError:
        pass
    return vals


def obtain_cookie_by_qr(cfg):
    """运行扫码工具获取 Cookie，回读 api.txt 确认保存，并用诊断工具验证有效性。

    返回 True 表示 Cookie 已获取并验证通过。
    """
    qr_script = os.path.join(ROOT, "mihoyo", "miyoushe_qr_login.py")
    debug_script = os.path.join(ROOT, "mihoyo", "miyoushe_debug.py")

    print("\n  即将启动扫码工具：用手机米游社 App 扫二维码并确认登录，")
    print("  成功后会自动把 Cookie 写入 api.txt。扫码过程中可随时 Ctrl+C 取消。")
    if not ask_yn("是否继续？", default_yes=True):
        return False

    rc = subprocess.run([sys.executable, qr_script]).returncode
    if rc != 0:
        print("  [!] 扫码未完成（已取消 / 超时 / 失败）")
        return False

    # 回读 api.txt，确认 Cookie 已保存
    saved = read_api_file_values(("MIYOUSHE_COOKIE", "DEVICE_ID"))
    if not saved.get("MIYOUSHE_COOKIE"):
        print("  [!] api.txt 中未找到已保存的 Cookie，视为失败")
        return False
    cfg["MIYOUSHE_COOKIE"] = saved["MIYOUSHE_COOKIE"]
    if saved.get("DEVICE_ID"):
        cfg["DEVICE_ID"] = saved["DEVICE_ID"]
    print("  [OK] Cookie 已保存到 api.txt")

    # 用诊断工具验证 Cookie 合法性（只读检测，不会签到）
    print("\n  正在运行诊断工具验证 Cookie 是否有效...\n")
    r = subprocess.run([sys.executable, debug_script])
    if r.returncode == 0:
        print("\n  [OK] Cookie 验证通过")
        return True
    print("\n  [!] 诊断工具报告 Cookie 异常，建议重试扫码或检查网络")
    return False


def collect_credentials(cfg):
    print("\n---- 步骤 2/4 游戏凭证 ----")
    if ask_yn("是否已有森空岛 Token？（明日方舟、终末地需要，获取方法见 README 第 2.1 节）"):
        cfg["SKLAND_TOKEN"] = ask_nonempty("请输入 SKLAND_TOKEN（多账号用英文逗号分隔）")
    else:
        print("  跳过：将不签到明日方舟 / 终末地（README 第 2.1 节有获取教程）")

    print("\n---- 米游社 Cookie（原神、星铁、绝区零需要）----")
    if ask_yn("是否已有米游社 Cookie？"):
        cfg["MIYOUSHE_COOKIE"] = ask(
            "请输入 MIYOUSHE_COOKIE（多账号用英文逗号分隔）",
            validator=cookie_format_ok, errmsg=COOKIE_ASK_ERRMSG)
    else:
        while True:
            if not ask_yn("是否现在运行扫码工具自动获取？", default_yes=True):
                print("  跳过：将不签到原神 / 星铁 / 绝区零（README 第 2.2 节有扫码教程）")
                break
            if obtain_cookie_by_qr(cfg):
                break
            choice = ask("\n扫码获取失败。1=重试扫码  2=手动输入  3=跳过米游社",
                         default="1",
                         validator=lambda v: v in ("1", "2", "3"),
                         errmsg="请输入 1、2 或 3")
            if choice == "2":
                cfg["MIYOUSHE_COOKIE"] = ask(
                    "请输入 MIYOUSHE_COOKIE（多账号用英文逗号分隔）",
                    validator=cookie_format_ok, errmsg=COOKIE_ASK_ERRMSG)
                break
            if choice == "3":
                break

    games = []
    if cfg.get("SKLAND_TOKEN"):
        games += ["1", "2"]
    if cfg.get("MIYOUSHE_COOKIE"):
        games += ["3", "4", "5"]
    if not games:
        print("[X] 至少需要一种凭证才能签到")
        raise Cancelled()
    cfg["SIGN_GAMES"] = ",".join(games)
    print(f"  已自动选择签到序号: {cfg['SIGN_GAMES']}（可在 api.txt 中修改）")


# ================== 通知渠道收集 ==================

NOTIFY_MENU = """
可选通知渠道（只包含已测试稳定的渠道）：
  1. Discord
  2. Telegram     （需要 BOT_TOKEN 和 CHAT_ID 两项）
  3. 企业微信
  4. 飞书
  5. 钉钉         （支持加签）
  6. Server酱     （推送到个人微信）
  7. 自定义 Webhook
  8. 邮件         （SMTP，推送到邮箱）
多选示例: 输入 2,5 表示同时配置 Telegram 和钉钉；直接回车 = 不使用外部通知
"""

URL_PREFIXES = {
    "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/",
    "WECHAT_WEBHOOK_URL": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=",
    "FEISHU_WEBHOOK_URL": "https://open.feishu.cn/open-apis/bot/v2/hook/",
}


def collect_notify(cfg):
    print("\n---- 步骤 3/4 通知渠道 ----")
    if not ask_yn("签到结果是否需要发送到外部通知？", default_yes=False):
        print("  跳过：不配置外部通知")
        return

    sel = ask(NOTIFY_MENU + "请选择要配置的渠道序号", default="",
              validator=lambda v: all(c.strip() in "12345678" and c.strip() for c in v.replace(" ", "").split(",") if c.strip()) or v == "",
              errmsg="只能输入 1-8 的数字，多个用英文逗号分隔")
    picks = {c.strip() for c in sel.replace(" ", "").split(",") if c.strip()}
    if not picks:
        print("  跳过：不配置外部通知")
        return

    for p in sorted(picks):
        if p == "1":
            cfg["DISCORD_WEBHOOK_URL"] = ask_url(
                "Discord Webhook 地址", URL_PREFIXES["DISCORD_WEBHOOK_URL"])
        elif p == "2":
            cfg["TELEGRAM_BOT_TOKEN"] = ask_nonempty("Telegram BOT_TOKEN")
            cfg["TELEGRAM_CHAT_ID"] = ask(
                "Telegram CHAT_ID（纯数字）",
                validator=lambda v: v.lstrip("-").isdigit(),
                errmsg="CHAT_ID 应为纯数字（@userinfobot 可查询）")
        elif p == "3":
            cfg["WECHAT_WEBHOOK_URL"] = ask_url(
                "企业微信机器人地址", URL_PREFIXES["WECHAT_WEBHOOK_URL"])
        elif p == "4":
            cfg["FEISHU_WEBHOOK_URL"] = ask_url(
                "飞书机器人地址", URL_PREFIXES["FEISHU_WEBHOOK_URL"])
        elif p == "5":
            cfg["DINGTALK_WEBHOOK_URL"] = ask_url(
                "钉钉机器人地址", "https://oapi.dingtalk.com/robot/send?access_token=")
            if ask_yn("钉钉安全设置是否选择了「加签」？", default_yes=False):
                secret = ask_nonempty("请输入加签密钥 SEC 开头的字符串")
                if not secret.startswith("SEC"):
                    secret = "SEC" + secret
                cfg["DINGTALK_SECRET"] = secret
        elif p == "6":
            cfg["SERVER_CHAN_KEY"] = ask_nonempty(
                "Server酱 SendKey（sct.ftqq.com 官网获取）")
        elif p == "7":
            cfg["CUSTOM_WEBHOOK_URL"] = ask(
                "自定义 Webhook 地址",
                validator=lambda v: v.startswith(("http://", "https://")),
                errmsg="必须以 http:// 或 https:// 开头")
        elif p == "8":
            cfg["SMTP_HOST"] = ask_nonempty("SMTP 服务器地址（如 smtp.qq.com）")
            cfg["SMTP_PORT"] = ask(
                "SMTP 端口（465=SSL，587=STARTTLS，直接回车=465）",
                default="465",
                validator=lambda v: v.isdigit() and 0 < int(v) < 65536,
                errmsg="端口应为数字")
            cfg["SMTP_USER"] = ask_nonempty("发件邮箱地址")
            cfg["SMTP_PASS"] = ask_nonempty("SMTP 授权码/密码（QQ、163 等需在邮箱设置中开启 SMTP 后生成授权码）")
            cfg["SMTP_TO"] = ask_nonempty("收件邮箱地址（多个用英文逗号分隔）")


# ================== 写入 api.txt ==================

TEMPLATE_ORDER = [
    "SKLAND_TOKEN", "MIYOUSHE_COOKIE", "DEVICE_ID", "SIGN_GAMES",
    "DISCORD_WEBHOOK_URL", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "WECHAT_WEBHOOK_URL", "FEISHU_WEBHOOK_URL",
    "DINGTALK_WEBHOOK_URL", "DINGTALK_SECRET",
    "SERVER_CHAN_KEY", "CUSTOM_WEBHOOK_URL",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_TO",
]


def write_api_file(cfg):
    """备份旧文件后写入新配置，返回备份路径（无旧文件则为 None）"""
    bak = None
    if os.path.exists(API_FILE):
        bak = API_FILE + ".bak"
        with open(API_FILE, encoding="utf-8") as f:
            with open(bak, "w", encoding="utf-8") as b:
                b.write(f.read())

    lines = ["# 由 setup_sign.py 自动生成", "# 手动修改后重新运行 sign_all.py 即生效", ""]
    for key in TEMPLATE_ORDER:
        val = cfg.get(key, "")
        # shell 安全引用：Cookie 等值含分号时，直接写入会被 source 截断
        lines.append(f"{key}={shlex.quote(val)}" if val else f"{key}=")
    with open(API_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(API_FILE, 0o600)   # 含敏感凭证，仅所有者可读写
    return bak


def rollback(bak):
    """测试失败时回退：恢复备份或删除新生成的配置"""
    if bak and os.path.exists(bak):
        os.replace(bak, API_FILE)
        print("  已回退到之前的 api.txt 配置")
    elif os.path.exists(API_FILE):
        os.remove(API_FILE)
        print("  新生成的 api.txt 已删除")


# ================== 测试运行 ==================

# 全部通知相关配置键（重新设置通知渠道时用于清空旧值）
NOTIFY_CFG_KEYS = [
    "DISCORD_WEBHOOK_URL", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "WECHAT_WEBHOOK_URL", "FEISHU_WEBHOOK_URL",
    "DINGTALK_WEBHOOK_URL", "DINGTALK_SECRET",
    "SERVER_CHAN_KEY", "CUSTOM_WEBHOOK_URL",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_TO"]


def _has_any_notify(cfg):
    return any(cfg.get(k) for k in NOTIFY_CFG_KEYS)


def test_notify_interactive(cfg, results):
    """发送测试通知并等待用户回复是否收到。

    - 收到 → 通过，继续后续流程
    - 未收到 → 询问是否重新设置外部通知渠道：
        * 选 y：清空旧配置重新收集，并再次发送测试（循环直到确认收到）
        * 选 n：跳过，继续步骤 4/4 测试与定时
    """
    import importlib
    import notify
    notify.DEBUG_NOTIFY = False

    while True:
        print("\n[测试] 发送测试通知...")
        res = notify.send_notification(
            "签到配置向导", "这是一条配置测试消息，收到即代表通知渠道正常。")
        results["notify"] = res
        bad = [name for name, status in (res or []) if status != "OK"]
        if bad:
            print(f"  [FAIL] 以下渠道接口返回失败: {', '.join(bad)}")
        else:
            print("  [OK] 接口全部返回成功")

        # 等待用户确认是否实际收到（输入不合法会循环提示；Ctrl+C 干净退出）
        if ask_yn("请查看对应平台，是否收到这条测试通知？"):
            return True

        if not ask_yn("是否重新设置外部通知渠道？", default_yes=True):
            print("  保持当前通知配置，继续后续步骤")
            return True

        # 清空旧通知配置后重新收集
        for k in NOTIFY_CFG_KEYS:
            cfg.pop(k, None)
            os.environ.pop(k, None)
        collect_notify(cfg)
        if not _has_any_notify(cfg):
            print("  未配置任何通知渠道，跳过通知测试")
            return True
        # 注入新值并让 notify 重新读取（模块在导入时读取环境变量）
        for k in NOTIFY_CFG_KEYS:
            os.environ[k] = cfg.get(k, "")
        importlib.reload(notify)


def run_tests(cfg):
    """返回 dict: {"notify": [(名称,状态)...] 或 None, "cred_ok": bool}"""
    # 把配置注入当前进程环境供 notify 使用
    for k, v in cfg.items():
        os.environ[k] = v
    sys.path.insert(0, ROOT)

    results = {"notify": None}

    # 1) 凭证连通性
    cred_ok = True
    if cfg.get("SKLAND_TOKEN"):
        print("\n[测试] 森空岛 Token 连通性...")
        try:
            from skland.skland_common import parse_token, get_grant_code
            token_list = [t.strip() for t in cfg["SKLAND_TOKEN"].split(",") if t.strip()]
            for i, t in enumerate(token_list, 1):
                get_grant_code(parse_token(t))
                print(f"  [OK] 账号{i}")
        except SystemExit:
            raise
        except Exception as e:
            cred_ok = False
            print(f"  [FAIL] {str(e)[:120]}")
    if cfg.get("MIYOUSHE_COOKIE"):
        print("\n[测试] 米游社 Cookie 连通性...")
        try:
            from mihoyo.miyoushe_sign import parse_cookie, build_web_cookie
            cookie_list = [c.strip() for c in cfg["MIYOUSHE_COOKIE"].split(",") if c.strip()]
            for i, c in enumerate(cookie_list, 1):
                build_web_cookie(parse_cookie(c))
                print(f"  [OK] 账号{i}")
        except SystemExit:
            raise
        except Exception as e:
            cred_ok = False
            print(f"  [FAIL] {str(e)[:120]}")

    # 2) 通知渠道发送测试（交互确认是否收到，未收到可重设渠道）
    if _has_any_notify(cfg):
        test_notify_interactive(cfg, results)
    return results, cred_ok


# ================== 定时任务 ==================

def ask_int(prompt, lo, hi, default):
    return int(ask(f"{prompt}（{lo}-{hi}）", default=str(default),
                   validator=lambda v: v.isdigit() and lo <= int(v) <= hi,
                   errmsg=f"请输入 {lo}-{hi} 的整数"))


def install_crontab(line):
    """把 line 写入 crontab（幂等：替换旧的 sign-myself 条目），返回是否成功"""
    try:
        cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        old = cur.stdout if cur.returncode == 0 else ""
    except FileNotFoundError:
        print("[X] 系统缺少 crontab 命令，请手动添加以下内容到你的定时任务：")
        print(f"    {line}")
        return False

    kept = [l for l in old.splitlines() if "sign-myself" not in l]
    kept.append(line)
    new_cron = "\n".join(kept) + "\n"
    r = subprocess.run(["crontab", "-"], input=new_cron, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[X] crontab 写入失败: {r.stderr[:100]}")
        return False
    print("[OK] 已写入 crontab")
    return True


def show_local_time(hour, minute):
    """根据系统时区换算展示实际执行时刻（时区数据缺失时退回北京时间）"""
    BJ = timezone(timedelta(hours=8))
    try:
        local = datetime.now(BJ).replace(hour=hour, minute=minute,
                                         second=0, microsecond=0).astimezone()
        if local.utcoffset() == BJ.utcoffset():
            return local.strftime("%H:%M"), "北京时间"
        return local.strftime("%H:%M"), f"本地时间({local.tzname()})"
    except Exception:
        t = datetime.now(BJ).replace(hour=hour, minute=minute)
        return t.strftime("%H:%M"), "北京时间"


# ================== 主流程 ==================

def main():
    check_python()
    check_deps()

    print("=" * 46)
    print(" 每日签到 一键配置向导")
    print(" 任何一步按 Ctrl+C 取消并退出（不会保存）")
    print("=" * 46)

    cfg = {}

    # 步骤 2 凭证（失败可反复重填）
    while True:
        try:
            collect_credentials(cfg)
            break
        except Cancelled:
            print("\n已取消，未做任何更改")
            sys.exit(130)

    # 步骤 3 通知
    while True:
        try:
            collect_notify(cfg)
            break
        except Cancelled:
            print("\n已取消，未做任何更改")
            sys.exit(130)

    # 步骤 4/4 前置：写 api.txt 并测试，失败则回退重填
    print("\n---- 步骤 4/4 测试与定时 ----")
    while True:
        bak = write_api_file(cfg)
        try:
            _, cred_ok = run_tests(cfg)
        except Cancelled:
            print("\n已取消，未做任何更改")
            sys.exit(130)
        if cred_ok:
            print("\n[OK] 测试通过")
            break

        choice = ask(
            "\n测试未完全通过。1=重新填写参数  2=忽略并继续",
            default="1",
            validator=lambda v: v in ("1", "2"),
            errmsg="请输入 1 或 2")
        if choice == "2":
            break
        rollback(bak)
        cfg = {}
        try:
            collect_credentials(cfg)
            collect_notify(cfg)
        except Cancelled:
            print("\n已取消，未做任何更改")
            sys.exit(130)
        continue

    # 时间配置
    hour = ask_int("每天几点运行（小时）", 0, 23, 3)
    minute = ask_int("几点几分（分钟）", 0, 59, 25)
    local_hm, tz_tag = show_local_time(hour, minute)

    proj_dir = os.path.abspath(ROOT)
    log_path = os.path.join(proj_dir, "sign.log")
    cron_line = (f'{minute} {hour} * * * cd "{proj_dir}" && '
                 f'bash run.sh >> "{log_path}" 2>&1  # sign-myself 每日签到')

    print(f"\n定时方案: 每天 {local_hm}（{tz_tag}）自动签到")

    if ask_yn("是否将以上定时任务写入 crontab？"):
        if not install_crontab(cron_line):
            print("    可稍后手动添加上面这行")
    else:
        print("  已跳过。之后如需启用，把下面这行加入 crontab 即可：")
        print(f"    {cron_line}")

    print("\n" + "=" * 46)
    print(" 配置完成！参数已保存到 api.txt（权限 600）")
    print(f" 手动测试命令: cd {proj_dir} && bash run.sh")
    print(" 日志文件: sign.log（可随时删除，不影响运行）")
    print("=" * 46)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消，未保存任何更改")
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        print(f"\n[X] 发生错误：{e}")
        if os.environ.get("DEBUG"):
            raise
        print("可设置 DEBUG=1 后重试以查看详细堆栈")
        sys.exit(1)
