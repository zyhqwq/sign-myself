#!/usr/bin/env python3
"""米游社扫码登录工具 - 本地运行，Cookie 用于 GitHub Actions 签到

使用网页端授权流程：扫码确认后直接下发完整 Cookie
（account_id / cookie_token / ltoken 等），不依赖 stoken 换取。

等待扫码策略：
- 单张二维码超过 SCAN_TIMEOUT 秒无人扫描或已过期时自动刷新，最多刷新 MAX_REFRESH 次
- 已扫描但长时间未在手机上确认：直接退出（避免作废手机端待确认的会话）
- 任何时刻按 Ctrl+C：干净退出，不写入任何文件
"""

import os
import random
import re
import shlex
import string
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
API_FILE = ROOT / "api.txt"

CREATE_QR_URL = "https://passport-api.mihoyo.com/account/ma-cn-passport/web/createQRLogin"
QUERY_QR_URL = "https://passport-api.mihoyo.com/account/ma-cn-passport/web/queryQRLoginStatus"

POLL_INTERVAL = 3
SCAN_TIMEOUT = 90       # 单张二维码等待被扫描的超时秒数
CONFIRM_TIMEOUT = 120   # 已扫描后等待手机确认的超时秒数
MAX_REFRESH = 3         # 未扫码时自动刷新二维码的次数上限


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

    print()
    print("获取可扫二维码的方式（任选其一）：")
    print("  1. 直接扫描上方终端二维码（若显示正常）")
    if files:
        print(f"  2. 打开脚本同目录下的 {' 或 '.join(files)}，用手机扫屏幕")
    print("  3. 把 login_url.txt 里的链接发到手机（微信文件传输助手等），")
    print("     用手机浏览器直接打开它 —— 效果等同于扫码确认")
    if files:
        print(f"  （二维码文件保存在：{ROOT}）")
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

    lines.append(f"MIYOUSHE_COOKIE={shlex.quote(cookie)}")
    lines.append(f"DEVICE_ID={shlex.quote(device_id)}")
    API_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(API_FILE, 0o600)
    print(f"✓ 已自动更新 {API_FILE}（原内容备份为 {bak.name if bak else '无'}）")


def poll_qr_status(session, ticket, device_id, timeout, target):
    """轮询二维码状态直到达到 target 状态 / 过期 / 超时。

    返回 ("reached", result, resp) | "expired" | "timeout"；查询接口持续异常按超时处理。
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            result, resp = query_qr_status(session, ticket, device_id)
        except Exception as e:
            print(f"  查询状态异常，重试中: {str(e)[:60]}")
            time.sleep(POLL_INTERVAL)
            continue

        retcode = result.get("retcode")
        if retcode == -3501:
            return "expired"
        if retcode != 0:
            print(f"\n查询失败: {result.get('message')} (retcode={retcode})")
            sys.exit(1)

        status = (result.get("data") or {}).get("status")
        if status == target:
            return "reached", result, resp
        time.sleep(POLL_INTERVAL)
    return "timeout"


def parse_cookie_str(cookie_str):
    cookies = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def extract_cookies(result, resp):
    """从 Confirmed 响应提取登录 Cookie。

    兼容三种下发位置（按优先级合并，互为补充）：
    1. JSON body 的 data.cookies 列表（[{name, value}, ...]）
    2. 原始 Set-Cookie 响应头（可能多条）
    3. requests 已解析的 cookie jar

    字段覆盖 v1 与 v2 两代凭证（新版网页登录仅下发 *_v2 系列）。
    """
    order = ["stoken", "stuid", "ltoken", "ltoken_v2", "ltid", "mid",
             "ltmid_v2", "account_id", "account_mid_v2",
             "cookie_token", "cookie_token_v2", "euid", "devicefp"]
    keep = set(order)
    jar = {}

    def put(name, value):
        if name in keep and value and not jar.get(name):
            jar[name] = value

    # 1) JSON body
    data = result.get("data") or {}
    body_cookies = data.get("cookies") or []
    if isinstance(body_cookies, dict):
        body_cookies = [body_cookies]
    for item in body_cookies:
        if isinstance(item, dict):
            put(item.get("name"), item.get("value"))

    # 2) 原始 Set-Cookie 头
    try:
        raw_headers = resp.raw.headers.getlist("Set-Cookie")
    except Exception:
        raw_headers = []
    for raw in raw_headers:
        first = raw.split(";", 1)[0].strip()
        if "=" in first:
            k, v = first.split("=", 1)
            put(k.strip(), v.strip())

    # 3) requests cookie jar
    try:
        for c in resp.cookies:
            put(c.name, c.value)
    except Exception:
        pass

    return ";".join(f"{k}={jar[k]}" for k in order if k in jar)


def main():
    print("=" * 60)
    print("米游社扫码登录工具（本地运行，Cookie 用于 GitHub Actions 签到）")
    print("=" * 60)
    print("提示：等待扫码时可随时 Ctrl+C 取消，不会修改任何文件")

    session = requests.Session()
    device_id = random_string(16)
    refresh_left = MAX_REFRESH

    # ---- 阶段一：生成二维码并等待扫描（超时/过期自动刷新，最多 MAX_REFRESH 次）----
    while True:
        try:
            qr_url, ticket = create_qr_login(session, device_id)
        except Exception as e:
            print(f"错误: 创建二维码失败 - {e}")
            sys.exit(1)

        extra = f"（自动刷新剩余 {refresh_left} 次）" if refresh_left != MAX_REFRESH else ""
        print(f"\n请使用米游社 App 扫描下方二维码{extra}")
        render_qr(qr_url)
        print(f"等待扫码中（{SCAN_TIMEOUT} 秒内未扫将自动刷新）...\n")

        try:
            state = poll_qr_status(session, ticket, device_id, SCAN_TIMEOUT, "Scanned")
        except KeyboardInterrupt:
            print("\n\n已取消：未获取到登录凭证，api.txt 未做任何修改")
            sys.exit(130)

        if isinstance(state, tuple):   # ("reached", resp)：已被扫描
            print("✓ 已扫描，请在手机上点击确认登录...")
            break

        reason = "二维码已过期" if state == "expired" else "迟迟未扫码"

        if refresh_left > 0:
            refresh_left -= 1
            print(f"[!] {reason}，自动刷新二维码（剩余 {refresh_left} 次刷新机会）")
            continue

        print(f"[X] {reason}，且刷新次数已用完，退出。需要时请重新运行本工具")
        sys.exit(1)

    # ---- 阶段二：已扫描，等待手机确认（不刷新，避免作废手机端会话）----
    try:
        state = poll_qr_status(session, ticket, device_id,
                               CONFIRM_TIMEOUT, "Confirmed")
    except KeyboardInterrupt:
        print("\n\n已取消：未获取到登录凭证，api.txt 未做任何修改")
        sys.exit(130)

    if state == "timeout":
        print("\n[X] 已扫码但长时间未在手机上确认，退出。请重新运行本工具")
        sys.exit(1)
    if state == "expired":
        print("\n[X] 二维码在确认前过期，退出。请重新运行本工具")
        sys.exit(1)

    _, result, resp = state
    if resp is None:
        print("\n登录流程异常，请重试")
        sys.exit(1)

    cookie = extract_cookies(result, resp)
    if not cookie:
        # 打印实际下发内容帮助定位（值全部脱敏）
        body_keys = list((result.get("data") or {}).keys())
        try:
            header_names = [h.split("=", 1)[0] for h in
                            resp.raw.headers.getlist("Set-Cookie")]
        except Exception:
            header_names = []
        print(f"错误: 未获取到可用 Cookie。body keys={body_keys}，"
              f"Set-Cookie 字段={header_names}")
        sys.exit(1)

    fields = ", ".join(
        f"{k}({len(v)}位)" for k, v in parse_cookie_str(cookie).items())
    print(f"已捕获字段: {fields}")

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
