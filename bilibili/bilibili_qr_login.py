#!/usr/bin/env python3
"""Bilibili 扫码登录工具 - 本地运行，输出 GitHub Actions 所需的三个 Cookie 值

使用 B 站网页端扫码登录流程：扫码确认后从 Set-Cookie 中提取
SESSDATA / DedeUserID / bili_jct，分别对应 Secret
BILI_SESSDATA / BILI_DEDEUSERID / BILI_JCT。

等待扫码策略：
- 单张二维码超过 SCAN_TIMEOUT 秒无人扫描或已过期时自动刷新，最多刷新 MAX_REFRESH 次
- 已扫描但长时间未在手机上确认：直接退出（避免作废手机端待确认的会话）
- 任何时刻按 Ctrl+C：干净退出

多账号：一次运行结束后可选择继续扫码下一个账号，
各字段自动用英文逗号连接，与 Secrets 的多账号格式一致。
"""

import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent

GEN_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
POLL_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Referer": "https://www.bilibili.com/"}

POLL_INTERVAL = 2
SCAN_TIMEOUT = 90       # 单张二维码等待被扫描的超时秒数
CONFIRM_TIMEOUT = 120   # 已扫描后等待手机确认的超时秒数
MAX_REFRESH = 3         # 未扫码时自动刷新二维码的次数上限

# 轮询状态码（data.code）
ST_WAIT_SCAN = 86101    # 未扫码
ST_SCANNED = 86090      # 已扫码未确认
ST_EXPIRED = 86038      # 二维码已失效


def create_qr(session):
    """创建扫码登录，返回 (二维码链接, qrcode_key)"""
    resp = session.get(GEN_URL, headers=HEADERS, timeout=15)
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"创建二维码失败: {data.get('message')}")
    return data["data"]["url"], data["data"]["qrcode_key"]


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
        svg_path = ROOT / "bilibili_login_qr.svg"
        qr.make_image(image_factory=SvgPathImage).save(str(svg_path))
        files.append(svg_path.name)

        png_path = ROOT / "bilibili_login_qr.png"
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
        print(f"  2. 打开脚本同目录下的 {' 或 '.join(files)}，用手机扫屏幕")
    print()


def poll_once(session, key):
    """查询一次状态，返回 (data_code, resp)"""
    resp = session.get(POLL_URL, params={"qrcode_key": key},
                       headers=HEADERS, timeout=15)
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"查询状态失败: {data.get('message')}")
    d = data.get("data") or {}
    return d.get("code"), resp


def wait_scan(session, key):
    """等待被扫描；返回 True 表示已扫描。超时/过期自动处理由外层控制"""
    start = time.time()
    while time.time() - start < SCAN_TIMEOUT:
        try:
            code, _ = poll_once(session, key)
        except Exception as e:
            print(f"  查询状态异常，重试中: {str(e)[:60]}")
            time.sleep(POLL_INTERVAL)
            continue
        if code == ST_SCANNED:
            return True
        if code == ST_EXPIRED:
            return False
        time.sleep(POLL_INTERVAL)
    return False


def wait_confirm(session, key):
    """已扫描后等待手机确认；成功返回响应对象，失败返回 None"""
    start = time.time()
    print("✓ 已扫描，请在手机上点击确认登录...")
    while time.time() - start < CONFIRM_TIMEOUT:
        try:
            code, resp = poll_once(session, key)
        except Exception as e:
            print(f"  查询状态异常，重试中: {str(e)[:60]}")
            time.sleep(POLL_INTERVAL)
            continue
        if code == 0:
            return resp
        if code == ST_EXPIRED:
            print("\n[X] 二维码在确认前过期，退出。请重新运行本工具")
            return None
        time.sleep(POLL_INTERVAL)
    print("\n[X] 已扫码但长时间未在手机上确认，退出。请重新运行本工具")
    return None


def extract_cookies(resp):
    """从成功响应中提取 SESSDATA / DedeUserID / bili_jct"""
    want = ["SESSDATA", "DedeUserID", "bili_jct"]
    jar = {}
    try:
        raw_headers = resp.raw.headers.getlist("Set-Cookie")
    except Exception:
        raw_headers = []
    for raw in raw_headers:
        first = raw.split(";", 1)[0].strip()
        if "=" in first:
            k, v = first.split("=", 1)
            k = k.strip()
            if k in want and not jar.get(k):
                jar[k] = v.strip()
    for c in getattr(resp, "cookies", []):
        if c.name in want and not jar.get(c.name):
            jar[c.name] = c.value
    return jar


def scan_one_account(session):
    """完成一次扫码登录，返回字段 dict 或 None"""
    refresh_left = MAX_REFRESH
    while True:
        try:
            qr_url, key = create_qr(session)
        except Exception as e:
            print(f"错误: 创建二维码失败 - {e}")
            return None

        extra = f"（自动刷新剩余 {refresh_left} 次）" if refresh_left != MAX_REFRESH else ""
        print(f"\n请使用哔哩哔哩 App 扫描下方二维码{extra}")
        render_qr(qr_url)
        print(f"等待扫码中（{SCAN_TIMEOUT} 秒内未扫将自动刷新）...\n")

        try:
            scanned = wait_scan(session, key)
        except KeyboardInterrupt:
            print("\n\n已取消")
            sys.exit(130)

        if scanned:
            break

        reason = "二维码已过期" if wait_scan_result_is_expired(session, key) else "迟迟未扫码"
        if refresh_left > 0:
            refresh_left -= 1
            print(f"[!] {reason}，自动刷新二维码（剩余 {refresh_left} 次刷新机会）")
            continue
        print(f"[X] {reason}，且刷新次数已用完，退出。需要时请重新运行本工具")
        return None

    try:
        resp = wait_confirm(session, key)
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(130)
    if resp is None:
        return None

    cookies = extract_cookies(resp)
    missing = [k for k in ("SESSDATA", "DedeUserID") if not cookies.get(k)]
    if missing:
        print(f"[X] 未获取到完整 Cookie（缺少 {', '.join(missing)}），请重试")
        return None
    return cookies


def wait_scan_result_is_expired(session, key):
    """区分超时与过期（仅用于提示文案，查询失败按超时处理）"""
    try:
        code, _ = poll_once(session, key)
        return code == ST_EXPIRED
    except Exception:
        return False


def main():
    print("=" * 60)
    print("Bilibili 扫码登录工具（本地运行，Cookie 用于 GitHub Actions 登录）")
    print("=" * 60)
    print("提示：等待扫码时可随时 Ctrl+C 取消")

    session = requests.Session()
    accounts = []
    while True:
        cookies = scan_one_account(session)
        if cookies is None:
            if not accounts:
                sys.exit(1)
            break
        accounts.append(cookies)
        sd = [a["SESSDATA"] for a in accounts]
        dd = [a["DedeUserID"] for a in accounts]
        jc = [a["bili_jct"] for a in accounts if a.get("bili_jct")]

        print("\n" + "=" * 60)
        print(f"第 {len(accounts)} 个账号获取成功！当前累计结果：")
        print("-" * 60)
        print(f"BILI_SESSDATA   = {','.join(sd)}")
        print(f"BILI_DEDEUSERID = {','.join(dd)}")
        if jc:
            print(f"BILI_JCT        = {','.join(jc)}")
        print("-" * 60)
        print("分别复制填入同名 Secret 即可（各字段已自动用英文逗号连接）")

        try:
            more = input("\n是否继续扫码添加下一个账号？(y/N)：").strip().lower()
        except KeyboardInterrupt:
            print("\n\n已退出")
            break
        if more not in ("y", "yes"):
            break

    print("=" * 60)
    print("完成！如需重新获取，再次运行本脚本即可")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消，未保存任何更改")
        sys.exit(130)
