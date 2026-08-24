#!/usr/bin/env python3
"""共享通知模块 - 支持多种通知渠道"""

import os
import time
import json
import hmac
import hashlib
import base64
import traceback
import urllib.parse
import requests
from datetime import datetime

WECHAT_WEBHOOK_URL = os.environ.get('WECHAT_WEBHOOK_URL', '')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_WEBHOOK_URL', '')
DINGTALK_WEBHOOK_URL = os.environ.get('DINGTALK_WEBHOOK_URL', '')
DINGTALK_SECRET = os.environ.get('DINGTALK_SECRET', '')
BARK_URL = os.environ.get('BARK_URL', '')
PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN', '')
SERVER_CHAN_KEY = os.environ.get('SERVER_CHAN_KEY', '')
CUSTOM_WEBHOOK_URL = os.environ.get('CUSTOM_WEBHOOK_URL', '')
DEBUG_NOTIFY = os.environ.get('DEBUG_NOTIFY', '').lower() in ('true', '1', 'yes')


def _debug(verbose, tag, **info):
    if not verbose:
        return
    for key, val in info.items():
        if isinstance(val, dict):
            val = json.dumps(val, ensure_ascii=False)[:500]
        elif isinstance(val, str) and len(val) > 500:
            val = val[:500] + '...'
        print(f"    [{tag}] {key}: {val}")


def _send_custom_webhook(title, message, extra_data=None, verbose=False):
    try:
        data = {
            "event": "daily_sign",
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "source": "github_actions",
        }
        if extra_data:
            data.update(extra_data)

        _debug(verbose, "custom", url=CUSTOM_WEBHOOK_URL, format="json")

        try:
            resp = requests.post(CUSTOM_WEBHOOK_URL, json=data, timeout=15,
                                 headers={'Content-Type': 'application/json'})
            _debug(verbose, "custom", status=resp.status_code, body=resp.text)
            if resp.status_code in (200, 201, 202, 204):
                return "OK"
        except Exception as e:
            _debug(verbose, "custom", error=str(e))

        try:
            text_data = f"{title}\n\n{message}"
            resp = requests.post(CUSTOM_WEBHOOK_URL, data=text_data, timeout=15,
                                 headers={'Content-Type': 'text/plain'})
            _debug(verbose, "custom", status=resp.status_code, body=resp.text)
            if resp.status_code in (200, 201, 202, 204):
                return "OK (text)"
        except Exception as e:
            _debug(verbose, "custom", error=str(e))

        try:
            form_data = {"title": title, "message": message}
            resp = requests.post(CUSTOM_WEBHOOK_URL, data=form_data, timeout=15)
            _debug(verbose, "custom", status=resp.status_code, body=resp.text)
            if resp.status_code in (200, 201, 202, 204):
                return "OK (form)"
        except Exception as e:
            _debug(verbose, "custom", error=str(e))

        return "all formats failed"
    except Exception as e:
        _debug(verbose, "custom", exception=traceback.format_exc())
        return str(e)


def _send_wechat(title, message, verbose=False):
    payload = {"msgtype": "text", "text": {"content": f"【{title}】\n\n{message[:1500]}"}}
    for attempt in range(3):
        try:
            _debug(verbose, "wechat", url=WECHAT_WEBHOOK_URL, attempt=attempt + 1)
            resp = requests.post(WECHAT_WEBHOOK_URL, json=payload, timeout=15,
                                 headers={'Content-Type': 'application/json'})
            _debug(verbose, "wechat", status=resp.status_code, body=resp.text)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("errcode") == 0:
                    return "OK"
                return result.get("errmsg", "failed")
            return f"HTTP {resp.status_code}"
        except Exception as e:
            _debug(verbose, "wechat", error=str(e))
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
            else:
                return str(e)
    return "max retries exceeded"


def _send_discord(title, message, verbose=False):
    try:
        content = f"**{title}**\n\n{message}"
        if "成功" in title:
            color = 3066993
        elif "失败" in title:
            color = 15158332
        else:
            color = 16776960
        payload = {
            "content": content[:2000],
            "embeds": [{"title": title, "description": message[:2000],
                        "color": color, "timestamp": datetime.now().isoformat()}]
        }
        _debug(verbose, "discord", url=DISCORD_WEBHOOK_URL)
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
        _debug(verbose, "discord", status=resp.status_code, body=resp.text)
        return "OK" if resp.status_code in (200, 204) else f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        _debug(verbose, "discord", exception=traceback.format_exc())
        return str(e)


def _send_telegram(title, message, verbose=False):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"<b>{title}</b>\n\n{message}",
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        _debug(verbose, "telegram", url=url, chat_id=TELEGRAM_CHAT_ID)
        resp = requests.post(url, json=payload, timeout=15)
        _debug(verbose, "telegram", status=resp.status_code, body=resp.text)
        return "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        _debug(verbose, "telegram", exception=traceback.format_exc())
        return str(e)


def _send_feishu(title, message, verbose=False):
    try:
        payload = {"msg_type": "text", "content": {"text": f"{title}\n\n{message}"}}
        _debug(verbose, "feishu", url=FEISHU_WEBHOOK_URL)
        resp = requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=15)
        result = resp.json()
        _debug(verbose, "feishu", status=resp.status_code, body=resp.text)
        return "OK" if result.get("code") == 0 else f"code={result.get('code')}: {result.get('msg', 'failed')}"
    except Exception as e:
        _debug(verbose, "feishu", exception=traceback.format_exc())
        return str(e)


def _send_dingtalk(title, message, verbose=False):
    try:
        payload = {"msgtype": "text", "text": {"content": f"【通知】{title}\n\n{message}"}}
        url = DINGTALK_WEBHOOK_URL

        if DINGTALK_SECRET:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f'{timestamp}\n{DINGTALK_SECRET}'
            hmac_code = hmac.new(
                DINGTALK_SECRET.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            url = f'{url}&timestamp={timestamp}&sign={sign}'

        _debug(verbose, "dingtalk", url=url, signed=bool(DINGTALK_SECRET))
        resp = requests.post(url, json=payload, timeout=15)
        result = resp.json()
        _debug(verbose, "dingtalk", status=resp.status_code, body=resp.text)
        return "OK" if result.get("errcode") == 0 else f"errcode={result.get('errcode')}: {result.get('errmsg', 'failed')}"
    except Exception as e:
        _debug(verbose, "dingtalk", exception=traceback.format_exc())
        return str(e)


def _send_bark(title, message, verbose=False):
    try:
        body = message.replace("\n", "\\n")[:100]
        url = f"{BARK_URL.rstrip('/')}/{title}/{body}"
        _debug(verbose, "bark", url=url)
        resp = requests.get(url, timeout=15)
        _debug(verbose, "bark", status=resp.status_code, body=resp.text)
        return "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        _debug(verbose, "bark", exception=traceback.format_exc())
        return str(e)


def _send_pushplus(title, message, verbose=False):
    try:
        url = "https://www.pushplus.plus/send"
        payload = {"token": PUSHPLUS_TOKEN, "title": title, "content": message, "template": "html"}
        _debug(verbose, "pushplus", url=url)
        resp = requests.post(url, json=payload, timeout=15)
        result = resp.json()
        _debug(verbose, "pushplus", status=resp.status_code, body=resp.text)
        return "OK" if result.get("code") == 200 else f"code={result.get('code')}: {result.get('msg', 'failed')}"
    except Exception as e:
        _debug(verbose, "pushplus", exception=traceback.format_exc())
        return str(e)


def _send_serverchan(title, message, verbose=False):
    try:
        url = f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send"
        payload = {"title": title, "desp": message}
        _debug(verbose, "serverchan", url=url)
        resp = requests.post(url, json=payload, timeout=15)
        result = resp.json()
        _debug(verbose, "serverchan", status=resp.status_code, body=resp.text)
        return "OK" if result.get("code") == 0 else f"code={result.get('code')}: {result.get('message', 'failed')}"
    except Exception as e:
        _debug(verbose, "serverchan", exception=traceback.format_exc())
        return str(e)


from datetime import timezone, timedelta

BEIJING_TZ = timezone(timedelta(hours=8))


def format_sign_entry(game: str, account: str, role: str,
                      result: str = "", award: str = "") -> str:
    """统一条目格式：■游戏名 / 账号 / 角色 / 签到结果 / 今日奖励 / 累计天数 / 北京时间"""
    lines = [
        f"■ {game}",
        f"账号: {account}",
        f"角色: {role}",
    ]
    if result:
        bad = any(k in result for k in ("失败", "异常", "失效", "风控"))
        lines.append(f"{'❌' if bad else '✅'} {result}")
    if award:
        lines.append(f"今日奖励: {award}")
    when = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"签到时间: {when}")
    return "\n".join(lines)


def send_notification(title: str, message: str, extra_data=None, verbose=False):
    """发送通知到所有已配置的渠道"""
    # 聚合模式：由统一入口(sign_all.py)设置，子任务只落盘不发送，
    # 最后由入口读取所有报告合并成一条通知发送
    agg_dir = os.environ.get("SIGN_REPORT_DIR", "")
    if agg_dir:
        try:
            os.makedirs(agg_dir, exist_ok=True)
            existing = [f for f in os.listdir(agg_dir) if f.endswith(".txt")]
            seq = len(existing)
            safe = "".join(c for c in title if c not in '\\/:*?"<>|').strip() or "report"
            with open(os.path.join(agg_dir, f"{seq:02d}_{safe}.txt"), "w", encoding="utf-8") as f:
                f.write(message)
            return [("汇总暂存", "OK")]
        except Exception:
            pass  # 落盘失败则回退为直接发送

    verbose = verbose or DEBUG_NOTIFY
    results = []

    if CUSTOM_WEBHOOK_URL:
        results.append(("自定义Webhook", _send_custom_webhook(title, message, extra_data, verbose)))
    if WECHAT_WEBHOOK_URL:
        results.append(("企业微信", _send_wechat(title, message, verbose)))
    if DISCORD_WEBHOOK_URL:
        results.append(("Discord", _send_discord(title, message, verbose)))
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        results.append(("Telegram", _send_telegram(title, message, verbose)))
    if FEISHU_WEBHOOK_URL:
        results.append(("飞书", _send_feishu(title, message, verbose)))
    if DINGTALK_WEBHOOK_URL:
        results.append(("钉钉", _send_dingtalk(title, message, verbose)))
    if BARK_URL:
        results.append(("Bark", _send_bark(title, message, verbose)))
    if PUSHPLUS_TOKEN:
        results.append(("PushPlus", _send_pushplus(title, message, verbose)))
    if SERVER_CHAN_KEY:
        results.append(("Server酱", _send_serverchan(title, message, verbose)))

    return results


def print_notify_results(results):
    """打印通知结果摘要"""
    if not results:
        print("\n 未配置任何通知渠道")
        return

    print("\n 通知发送结果：")
    has_failure = False
    for name, status in results:
        if status == "OK":
            print(f"   {name}: 成功")
        else:
            print(f"   {name}: {status}")
            has_failure = True

    if has_failure:
        print("\n💡 提示：设置 DEBUG_NOTIFY=true 可查看详细的请求/响应信息")


def get_webhook_status():
    """检查Webhook配置状态"""
    status = []
    checks = [
        (CUSTOM_WEBHOOK_URL, "自定义 Webhook"),
        (WECHAT_WEBHOOK_URL, "企业微信 Webhook"),
        (DISCORD_WEBHOOK_URL, "Discord Webhook"),
        (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, "Telegram Bot"),
        (FEISHU_WEBHOOK_URL, "飞书 Webhook"),
        (DINGTALK_WEBHOOK_URL, "钉钉 Webhook"),
        (BARK_URL, "Bark"),
        (PUSHPLUS_TOKEN, "PushPlus"),
        (SERVER_CHAN_KEY, "Server酱"),
    ]
    for configured, name in checks:
        status.append(f" {name} 已配置" if configured else f" {name} 未配置")
    return status
