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
import subprocess
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


def is_wsl():
    try:
        with open("/proc/version", encoding="utf-8") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def render_qr(url):
    """多通道输出二维码：终端 ASCII + SVG/PNG 文件 + 登录链接文件"""
    out_dir = Path(__file__).resolve().parent.parent

    # 登录链接单独保存：手机上直接打开该链接等同于扫码确认
    url_file = out_dir / "login_url.txt"
    url_file.write_text(url, encoding="utf-8")

    have_lib = True
    try:
        import qrcode
    except ImportError:
        have_lib = False

    files = []
    if have_lib:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,
                           box_size=1, border=1)
        qr.add_data(url)
        qr.make(fit=True)

        # 终端 ASCII（WSL/cmd 下可能渲染异常，仅作为快捷方式之一）
        qr.print_ascii(invert=True)

        # SVG：无需 pillow，浏览器直接打开即可展示
        try:
            from qrcode.image.svg import SvgPathImage
            img = qr.make_image(image_factory=SvgPathImage)
            svg_path = out_dir / "login_qr.svg"
            img.save(str(svg_path))
            files.append(svg_path.name)
        except Exception:
            pass

        # PNG：需 pillow，可用则一并生成
        try:
            img = qr.make_image(fill_color="black", back_color="white")
            png_path = out_dir / "login_qr.png"
            img.save(str(png_path))
            files.append(png_path.name)
        except Exception:
            pass
    else:
        print("[提示] 未安装 qrcode 库（pip install qrcode），仅提供链接方式")

    if is_wsl():
        # WSL：调用 Windows 资源管理器打开项目目录，方便双击图片文件
        try:
            subprocess.run(["explorer.exe", str(out_dir)], timeout=5,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            opened = "已尝试在 Windows 中打开项目目录"
        except Exception:
            opened = None

    print()
    print("获取可扫二维码的方式（任选其一）：")
    print(f"  1. 扫描上方终端二维码（若显示正常）")
    if files:
        print(f"  2. 在 Windows 里打开项目目录下的 {' 或 '.join(files)}，用手机扫屏幕")
    print(f"  3. 把 {url_file.name} 里的链接发到手机（微信文件传输助手等），")
    print(f"     用手机浏览器直接打开它 —— 效果等同于扫码确认")
    if is_wsl() and opened:
        print(f"  ({opened})")
    print()
    return True


def update_api_file(cookie, device_id):
    """若项目根目录存在 api.txt，则自动更新其中的 MIYOUSHE_COOKIE 与 DEVICE_ID 行"""
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
            if re.search(r"^DEVICE_ID=.*$", new_content, flags=re.M):
                new_content = re.sub(
                    r"^DEVICE_ID=.*$", f"DEVICE_ID={device_id}",
                    new_content, flags=re.M)
            else:
                new_content = new_content.rstrip("\n") + f"\nDEVICE_ID={device_id}\n"
        else:
            new_content = (content.rstrip("\n")
                           + f"\nMIYOUSHE_COOKIE={cookie}"
                           + f"\nDEVICE_ID={device_id}\n")
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
    update_api_file(cookie, device_id)
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
