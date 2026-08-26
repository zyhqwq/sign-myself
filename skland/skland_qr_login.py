#!/usr/bin/env python3
"""森空岛扫码登录工具 - 本地运行，Token 用于明日方舟/终末地签到

使用鹰角通行证网页扫码流程：森空岛 App 扫码确认后换取
鹰角网络通行证凭证（即 SKLAND_TOKEN），自动写入 api.txt。

等待扫码策略：
- 单张二维码超过 SCAN_TIMEOUT 秒无人扫描或已过期时自动刷新，最多刷新 MAX_REFRESH 次
- 已扫描但长时间未在手机上确认：直接退出（避免作废手机端待确认的会话）
- 任何时刻按 Ctrl+C：干净退出，不写入任何文件

多账号：一次运行结束后可选择继续扫码下一个账号，
多个 Token 自动用英文逗号连接，与 SKLAND_TOKEN 的多账号格式一致。
"""

import os
import shlex
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
API_FILE = ROOT / "api.txt"

GEN_URL = "https://as.hypergryph.com/general/v1/gen_scan/login"
STATUS_URL = "https://as.hypergryph.com/general/v1/scan_status"
TOKEN_URL = "https://as.hypergryph.com/user/auth/v1/token_by_scan_code"
BASIC_URL = "https://as.hypergryph.com/user/info/v1/basic"
APP_CODE = "4ca99fa6b56cc2ba"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
}

POLL_INTERVAL = 2
SCAN_TIMEOUT = 90       # 单张二维码等待被扫描的超时秒数
CONFIRM_TIMEOUT = 120   # 已扫描后等待手机确认的超时秒数
MAX_REFRESH = 3         # 未扫码时自动刷新二维码的次数上限


def create_scan(session):
    """创建扫码登录，返回 (二维码内容, scanId)"""
    resp = session.post(GEN_URL, json={"appCode": APP_CODE}, timeout=15)
    data = resp.json()
    if data.get("status") != 0:
        raise Exception(f"创建二维码失败: {data.get('msg')}")
    return data["data"]["scanUrl"], data["data"]["scanId"]


def poll_once(session, scan_id):
    """查询一次状态，返回 (status, msg, scanCode)；status==0 表示手机已确认"""
    resp = session.get(STATUS_URL, params={"scanId": scan_id},
                       headers=HEADERS, timeout=15)
    data = resp.json()
    status = data.get("status", -1)
    msg = data.get("msg", "")
    code = (data.get("data") or {}).get("scanCode") if status == 0 else None
    return status, msg, code


def render_qr(url):
    """多通道输出二维码：终端 ASCII + SVG/PNG 文件"""
    files = []
    try:
        import qrcode
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,
                           box_size=1, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)

        from qrcode.image.svg import SvgPathImage
        svg_path = ROOT / "skland_login_qr.svg"
        qr.make_image(image_factory=SvgPathImage).save(str(svg_path))
        files.append(svg_path.name)

        png_path = ROOT / "skland_login_qr.png"
        qr.make_image(fill_color="black", back_color="white").save(str(png_path))
        files.append(png_path.name)
    except ImportError:
        print("[提示] 未安装 qrcode 库（pip install qrcode），仅提供链接方式")
    except Exception as e:
        print(f"[提示] 图片生成失败({str(e)[:40]})，可使用下方链接方式")

    print()
    print("获取可扫二维码的方式（任选其一）：")
    print("  1. 直接扫描上方终端二维码（若显示正常）")
    if files:
        print(f"  2. 打开脚本同目录下的 {' 或 '.join(files)}，用另一台设备扫屏幕")
    print()


def exchange_token(session, scan_code):
    """用 scanCode 换取鹰角网络通行证凭证"""
    resp = session.post(TOKEN_URL, json={"scanCode": scan_code},
                        headers=HEADERS, timeout=15)
    data = resp.json()
    if data.get("status") != 0:
        raise Exception(f"获取 Token 失败: {data.get('msg')}")
    return data["data"]["token"]


def check_token(session, token):
    """校验 Token 有效性，返回账号描述；无效返回 None"""
    try:
        resp = session.get(BASIC_URL, params={"token": token}, timeout=15)
        data = resp.json()
        if data.get("status") != 0:
            return None
        info = data.get("data") or {}
        parts = [info.get(hg) for hg in ("hgId", "phone", "email") if info.get(hg)]
        return "/".join(str(p) for p in parts) or "未知账号"
    except Exception:
        return None


def update_api_file(token):
    """自动更新 api.txt 中的 SKLAND_TOKEN 行（追加或覆盖，保留其他配置）"""
    bak = None
    if API_FILE.exists():
        bak = API_FILE.with_name("api.txt.bak")
        bak.write_text(API_FILE.read_text(encoding="utf-8"), encoding="utf-8")

    lines = []
    for line in bak.read_text(encoding="utf-8").splitlines() if bak else []:
        if line.startswith("SKLAND_TOKEN="):
            continue
        lines.append(line)

    lines.append(f"SKLAND_TOKEN={shlex.quote(token)}")
    API_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(API_FILE, 0o600)


def scan_one_token(session):
    """完成一次扫码登录并校验，返回 token 字符串或 None"""
    refresh_left = MAX_REFRESH
    while True:
        try:
            qr_url, scan_id = create_scan(session)
        except Exception as e:
            print(f"错误: 创建二维码失败 - {e}")
            return None

        extra = f"（自动刷新剩余 {refresh_left} 次）" if refresh_left != MAX_REFRESH else ""
        print(f"\n请使用森空岛 App 扫描下方二维码{extra}")
        render_qr(qr_url)
        print(f"等待扫码中（{SCAN_TIMEOUT} 秒内未扫将自动刷新）...\n")

        # 阶段一：等待被扫描（过期自动刷新由外层控制）
        scanned = False
        expired = False
        start = time.time()
        while time.time() - start < SCAN_TIMEOUT:
            try:
                status, msg, _ = poll_once(session, scan_id)
            except Exception as e:
                print(f"  查询状态异常，重试中: {str(e)[:60]}")
                time.sleep(POLL_INTERVAL)
                continue
            if status == 0:
                scanned = True
                break
            time.sleep(POLL_INTERVAL)
        if scanned:
            break

        # 区分超时与二维码已失效（仅用于提示文案，查询失败按超时处理）
        reason = "迟迟未扫码"
        try:
            status, msg, _ = poll_once(session, scan_id)
            if status != 0 and ("过期" in msg or "失效" in msg):
                reason = "二维码已过期"
        except Exception:
            pass

        if refresh_left > 0:
            refresh_left -= 1
            print(f"[!] {reason}，自动刷新二维码（剩余 {refresh_left} 次刷新机会）")
            continue
        print(f"[X] {reason}，且刷新次数已用完，退出。需要时请重新运行本工具")
        return None

    # 阶段二：已扫描，等待手机确认
    print("✓ 已扫描，请在手机上点击确认登录...")
    scan_code = None
    start = time.time()
    while time.time() - start < CONFIRM_TIMEOUT:
        try:
            status, msg, code = poll_once(session, scan_id)
        except Exception as e:
            print(f"  查询状态异常，重试中: {str(e)[:60]}")
            time.sleep(POLL_INTERVAL)
            continue
        if status == 0 and code:
            scan_code = code
            break
        time.sleep(POLL_INTERVAL)
    if not scan_code:
        print("\n[X] 已扫码但长时间未在手机上确认，退出。请重新运行本工具")
        return None

    try:
        token = exchange_token(session, scan_code)
    except Exception as e:
        print(f"\n[X] {e}")
        return None

    who = check_token(session, token)
    if not who:
        print("\n[X] 获取到的 Token 校验未通过，请重试")
        return None
    return token, who


def main():
    print("=" * 60)
    print("森空岛扫码登录工具（本地运行，Token 用于 GitHub Actions 签到）")
    print("=" * 60)
    print("提示：等待扫码时可随时 Ctrl+C 取消")

    session = requests.Session()
    tokens = []
    while True:
        result = scan_one_token(session)
        if result is None:
            if not tokens:
                sys.exit(1)
            break
        token, who = result
        tokens.append(token)

        print("\n" + "=" * 60)
        print(f"第 {len(tokens)} 个账号获取成功！账号：{who}")
        print("-" * 60)
        print(f"SKLAND_TOKEN = {','.join(tokens)}")
        print("-" * 60)
        print("复制填入 Secret / api.txt 即可（多账号已自动用英文逗号连接）")

        try:
            more = input("\n是否继续扫码添加下一个账号？(y/N)：").strip().lower()
        except KeyboardInterrupt:
            print("\n\n已退出")
            break
        if more not in ("y", "yes"):
            break

    if not tokens:
        sys.exit(1)

    update_api_file(",".join(tokens))
    print("=" * 60)
    print("登录成功！Token 已自动写入 api.txt，无需手动复制")
    print("=" * 60)
    print("下一步: bash run.sh 验证签到是否正常")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消，未保存任何更改")
        sys.exit(130)
