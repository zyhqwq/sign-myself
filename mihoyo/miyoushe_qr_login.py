#!/usr/bin/env python3
"""米游社扫码登录工具 - 本地运行，Cookie 用于 GitHub Actions 签到

使用网页端授权流程：扫码确认后直接下发完整 Cookie
（account_id / cookie_token / ltoken 等），不依赖 stoken 换取。
"""

import os
import random
import re
import string
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
API_FILE = ROOT / "api.txt"

CREATE_QR_URL = "https://passport-api.mihoyo.com/account/ma-cn-passport/web/createQRLogin"
QUERY_QR_URL = "https://passport-api.mihoyo.com/account/ma-cn-passport/web/queryQRLoginStatus"

POLL_INTERVAL = 3
POLL_TIMEOUT = 300


def random_string(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def passport_headers(device_id):
    """网页端授权请求头"""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 12; Unspecified Device) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.129 Mobile "
            "Safari/537.36 miHoYoBBS/2.109.0"
        ),
        "x-rpc-app_id": "bll8iq97cem8",
        "x-rpc-client_type": "4",
        "x-rpc-device_id": device_id,
        "Origin": "https://user.mihoyo.com",
        "Referer": "https://user.mihoyo.com/",
        "Content-Type": "application/json",
    }


def create_qr_login(session, device_id):
    """创建扫码登录，返回 (二维码链接, ticket)"""
    resp = session.post(CREATE_QR_URL, headers=passport_headers(device_id),
                        json={}, timeout=15)
    data = resp.json()
    if data.get("retcode") != 0:
        raise Exception(f"创建二维码失败: {data.get('message')}")
    return data["data"]["url"], data["data"]["ticket"]


def query_qr_status(session, ticket, device_id):
    """轮询状态，返回 (json数据, 响应对象)；Confirmed 时需读取 Set-Cookie"""
    resp = session.post(QUERY_QR_URL, headers=passport_headers(device_id),
                        json={"ticket": ticket}, timeout=15)
    try:
        return resp.json(), resp
    except Exception:
        return {"retcode": -1, "message": "响应解析失败"}, resp


def is_wsl():
    try:
        with open("/proc/version", encoding="utf-8") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def render_qr(url):
    """多通道输出二维码：终端 ASCII + SVG/PNG 文件 + 登录链接文件"""
    url_file = ROOT / "login_url.txt"
    url_file.write_text(url, encoding="utf-8")

    files = []
    try:
        import qrcode
    except ImportError:
        print("[提示] 未安装 qrcode 库（pip install qrcode），仅提供链接方式")

    try:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,
                           box_size=1, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)

        from qrcode.image.svg import SvgPathImage
        svg_path = ROOT / "login_qr.svg"
        qr.make_image(image_factory=SvgPathImage).save(str(svg_path))
        files.append(svg_path.name)

        html_path = ROOT / "login_qr.html"
        svg_text = svg_path.read_text(encoding="utf-8")
        html_path.write_text(
            '<html><body style="text-align:center;margin-top:40px">'
            "<h3>米游社扫码登录</h3>"
            f"{svg_text}"
            "<p>请使用米游社 App 扫描此二维码</p></body></html>",
            encoding="utf-8")
        files.append(html_path.name)

        png_path = ROOT / "login_qr.png"
        qr.make_image(fill_color="black", back_color="white").save(str(png_path))
        files.append(png_path.name)
    except ImportError:
        pass
    except Exception as e:
        print(f"[提示] 图片生成失败({str(e)[:40]})，可使用下方链接方式")

    if is_wsl():
        def _open_dir():
            for p in ("explorer.exe", "/mnt/c/Windows/explorer.exe"):
                try:
                    subprocess.run([p, str(ROOT)], capture_output=True, timeout=8)
                    return
                except FileNotFoundError:
                    continue
                except Exception:
                    return
        import threading
        threading.Thread(target=_open_dir, daemon=True).start()

    print()
    print("获取可扫二维码的方式（任选其一）：")
    print("  1. 直接扫描上方终端二维码（若显示正常）")
    if files:
        print(f"  2. 打开项目目录下的 {' 或 '.join(files)}，用手机扫屏幕")
    print("  3. 把 login_url.txt 里的链接发到手机（微信文件传输助手等），")
    print("     用手机浏览器直接打开它 —— 效果等同于扫码确认")
    if is_wsl():
        print("  (WSL 环境：已尝试弹出 Windows 目录，未弹出请手动进入项目目录)")
    print()


def update_api_file(cookie, device_id):
    """自动更新 api.txt 中的 MIYOUSHE_COOKIE 与 DEVICE_ID 行"""
    bak = None
    if API_FILE.exists():
        bak = API_FILE.with_name("api.txt.bak")
        bak.write_text(API_FILE.read_text(encoding="utf-8"), encoding="utf-8")

    lines = []
    for line in bak.read_text(encoding="utf-8").splitlines() if bak else []:
        if line.startswith(("MIYOUSHE_COOKIE=", "DEVICE_ID=")):
            continue
        lines.append(line)

    lines.append(f"MIYOUSHE_COOKIE={cookie}")
    lines.append(f"DEVICE_ID={device_id}")
    API_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(API_FILE, 0o600)
    print(f"✓ 已自动更新 {API_FILE}（原内容备份为 {bak.name if bak else '无'}）")


def main():
    print("=" * 60)
    print("米游社扫码登录工具（本地运行，Cookie 用于 GitHub Actions 签到）")
    print("=" * 60)

    session = requests.Session()
    device_id = random_string(16)

    try:
        qr_url, ticket = create_qr_login(session, device_id)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

    render_qr(qr_url)
    print("等待扫码确认中...\n")

    scanned = False
    start = time.time()
    resp = None
    while time.time() - start < POLL_TIMEOUT:
        try:
            result, resp = query_qr_status(session, ticket, device_id)
        except Exception as e:
            print(f"查询状态异常，重试中: {e}")
            time.sleep(POLL_INTERVAL)
            continue

        retcode = result.get("retcode")
        if retcode == -3501:
            print("\n二维码已过期，请重新运行脚本")
            sys.exit(1)
        if retcode != 0:
            print(f"\n查询失败: {result.get('message')} (retcode={retcode})")
            sys.exit(1)

        status = (result.get("data") or {}).get("status")
        if status == "Scanned" and not scanned:
            scanned = True
            print("✓ 已扫描，请在手机上点击确认登录...")
        if status == "Confirmed":
            break

        time.sleep(POLL_INTERVAL)
    else:
        print("\n等待超时，请重新运行脚本")
        sys.exit(1)

    if result.get("retcode") != 0 or not resp:
        print("\n登录流程异常，请重试")
        sys.exit(1)

    # 网页授权：Confirmed 响应直接下发全套 Cookie
    keep = ["account_id", "cookie_token", "ltoken", "ltid", "mid", "euid", "stuid"]
    jar = {}
    for c in resp.cookies:
        if c.name in keep and c.value:
            jar[c.name] = c.value
    if not jar:
        raw = resp.headers.get("Set-Cookie", "")
        for part in re.split(r",(?=[^;]+?=)", raw):
            first = part.split(";")[0].strip()
            if "=" in first:
                k, v = first.split("=", 1)
                if k.strip() in keep:
                    jar[k.strip()] = v.strip()

    cookie = ";".join(f"{k}={jar[k]}" for k in keep if k in jar)
    if not cookie:
        print("错误: 未获取到 Cookie，请重试或改用手动抓包方式")
        sys.exit(1)

    update_api_file(cookie, device_id)

    print("=" * 60)
    print("登录成功！Cookie 已自动写入 api.txt，无需手动复制")
    print("=" * 60)
    print("下一步: bash run.sh 验证签到是否正常")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消，未保存任何更改")
        sys.exit(130)
