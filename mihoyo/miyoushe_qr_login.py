#!/usr/bin/env python3
"""米游社扫码登录工具 - 本地运行，获取 Cookie 后填入 GitHub Secrets

参考实现：
- TimeRainStarSky/TRSS-Plugin (Apps/miHoYoLogin.js) 扫码登录流程
- starudream/sign-task 米游社 API 请求头与 DS 签名

用法：
    python miyoushe_qr_login.py

流程：终端生成二维码 -> 米游社 App 扫码 -> 手机上确认登录 ->
     输出 Cookie -> 复制到仓库 Secret `MIYOUSHE_COOKIE`
"""

import json
import random
import re
import string
import sys
import time
from pathlib import Path

import requests

# ================== 接口地址（passport 扫码登录） ==================
CREATE_QR_URL = "https://passport-api.mihoyo.com/account/ma-cn-passport/app/createQRLogin"
QUERY_QR_URL = "https://passport-api.mihoyo.com/account/ma-cn-passport/app/queryQRLoginStatus"
COOKIE_TOKEN_URL = "https://passport-api.mihoyo.com/account/auth/api/getCookieAccountInfoBySToken"

# 二维码内容为登录页链接，米游社 App 扫码后确认登录
POLL_INTERVAL = 3          # 轮询间隔（秒）
POLL_TIMEOUT = 300         # 最长等待（秒）


def random_string(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def passport_headers(device_id):
    """扫码登录接口请求头（与 TRSS-Plugin app_request 一致）"""
    return {
        "User-Agent": "HYPContainer/1.3.3.182",
        "x-rpc-app_id": "ddxf5dufpuyo",
        "x-rpc-client_type": "3",
        "x-rpc-device_id": device_id,
    }


def create_qr_login():
    """创建扫码登录，返回 (二维码链接, ticket, device_id)"""
    device_id = random_string(16)
    resp = requests.post(
        CREATE_QR_URL, headers=passport_headers(device_id), json={}, timeout=15
    )
    data = resp.json()
    if data.get("retcode") != 0:
        raise Exception(f"创建二维码失败: {data}")
    return data["data"]["url"], data["data"]["ticket"], device_id


def query_qr_status(ticket, device_id):
    resp = requests.post(
        QUERY_QR_URL,
        headers=passport_headers(device_id),
        json={"ticket": ticket},
        timeout=15,
    )
    return resp.json()


def get_cookie_token(stoken, uid, mid):
    """用 stoken 换取 cookie_token"""
    url = f"{COOKIE_TOKEN_URL}?stoken={stoken}&uid={uid}&mid={mid}"
    resp = requests.get(
        url,
        headers=passport_headers(random_string(16)),
        cookies={"stoken": stoken, "stuid": uid, "mid": mid},
        timeout=15,
    )
    return resp.json()


def render_qr(url):
    """终端打印二维码；可选保存 PNG。依赖 qrcode 库（pip install qrcode）"""
    try:
        import qrcode
    except ImportError:
        print("未安装 qrcode 库，无法在终端显示二维码")
        print("请先执行: pip install qrcode")
        return False

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

    try:
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("miyoushe_qr.png")
        print("(已同时保存图片 miyoushe_qr.png，可用手机相册扫码)")
    except Exception:
        pass  # 未安装 pillow 时跳过 PNG 导出
    return True


def update_api_file(cookie):
    """若项目根目录存在 api.txt，则自动更新其中的 MIYOUSHE_COOKIE 行"""
    api_file = Path(__file__).resolve().parent.parent / "api.txt"
    if not api_file.exists():
        return False
    try:
        content = api_file.read_text(encoding="utf-8")
        bak = api_file.with_suffix(".txt.bak")
        bak.write_text(content, encoding="utf-8")
        if re.search(r"^MIYOUSHE_COOKIE=.*$", content, flags=re.M):
            new_content = re.sub(
                r"^MIYOUSHE_COOKIE=.*$", f"MIYOUSHE_COOKIE={cookie}",
                content, flags=re.M)
        else:
            new_content = content.rstrip("\n") + f"\nMIYOUSHE_COOKIE={cookie}\n"
        api_file.write_text(new_content, encoding="utf-8")
        print(f"已自动更新 {api_file} 中的 MIYOUSHE_COOKIE（原内容备份为 {bak.name}）")
        return True
    except Exception as e:
        print(f"自动更新 api.txt 失败（{e}），请手动复制上面的 Cookie")
        return False


def extract_cookie(result):
    """从 Confirmed 响应中提取完整 Cookie 字符串"""
    tokens = {t.get("name"): t.get("token") for t in result["data"].get("tokens", [])}
    user_info = result["data"].get("user_info", {})

    uid = user_info.get("aid") or user_info.get("uid") or user_info.get("account_id")
    mid = user_info.get("mid")
    stoken = tokens.get("stoken_v2") or tokens.get("stoken") or (
        next(iter(tokens.values()), None) if tokens else None
    )

    if not (uid and mid and stoken):
        print("错误: 无法提取 stoken/uid/mid，接口返回：")
        print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        return None

    parts = [f"stoken={stoken}", f"stuid={uid}", f"mid={mid}"]

    # 若返回中带 ltoken 则直接使用，否则用 stoken 换 cookie_token 补全
    ltoken = tokens.get("ltoken_v2") or tokens.get("ltoken")
    if ltoken:
        parts += [f"ltoken={ltoken}", f"ltuid={uid}"]
        print("✓ 已从登录结果获取 ltoken")

    cookie_result = get_cookie_token(stoken, uid, mid)
    if cookie_result.get("retcode") == 0 and cookie_result.get("data", {}).get("cookie_token"):
        parts.append(f"cookie_token={cookie_result['data']['cookie_token']}")
        print("✓ 已获取 cookie_token")
    else:
        print(f"提示: 获取 cookie_token 失败({cookie_result.get('message')})，不影响签到")

    nickname = user_info.get("nickname", "")
    if nickname:
        print(f"✓ 登录账号: {nickname} (UID {uid})")

    return ";".join(parts)


def main():
    print("=" * 60)
    print("米游社扫码登录工具（本地运行，Cookie 用于 GitHub Actions 签到）")
    print("=" * 60)

    try:
        qr_url, ticket, device_id = create_qr_login()
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

    print("\n请打开米游社 App -> 右上角扫一扫，扫描以下二维码：\n")
    if not render_qr(qr_url):
        print(f"\n请自行将以下链接生成二维码后用米游社 App 扫描：\n{qr_url}\n")

    print("\n等待扫码确认中...\n")

    scanned = False
    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        try:
            result = query_qr_status(ticket, device_id)
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

        status = result.get("data", {}).get("status")
        if status == "Scanned" and not scanned:
            scanned = True
            print("✓ 已扫描，请在手机上点击确认登录...")
        if status == "Confirmed":
            cookie = extract_cookie(result)
            break

        time.sleep(POLL_INTERVAL)
    else:
        print("\n等待超时，请重新运行脚本")
        sys.exit(1)

    if not cookie:
        sys.exit(1)

    print("=" * 60)
    print("登录成功！你的米游社 Cookie 如下：")
    update_api_file(cookie)
    print("=" * 60)
    print(cookie)
    print("=" * 60)
    print("请将其添加到 GitHub Secrets：")
    print("1. 进入你 Fork 的仓库 -> Settings -> Secrets and variables -> Actions")
    print("2. 点击 New repository secret")
    print("3. Name 填 MIYOUSHE_COOKIE，Value 粘贴上面整行 Cookie")
    print("4. 多账号：多个 Cookie 用英文逗号 , 分隔填入同一个 Secret")


if __name__ == "__main__":
    main()
