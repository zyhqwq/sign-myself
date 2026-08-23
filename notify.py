#!/usr/bin/env python3
"""共享通知模块 - 支持多种通知渠道"""

import os
import time
import requests
from datetime import datetime

WECHAT_WEBHOOK_URL = os.environ.get('WECHAT_WEBHOOK_URL', '')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_WEBHOOK_URL', '')
BARK_URL = os.environ.get('BARK_URL', '')
PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN', '')
SERVER_CHAN_KEY = os.environ.get('SERVER_CHAN_KEY', '')
CUSTOM_WEBHOOK_URL = os.environ.get('CUSTOM_WEBHOOK_URL', '')


def _send_custom_webhook(title, message, extra_data=None):
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

        try:
            resp = requests.post(CUSTOM_WEBHOOK_URL, json=data, timeout=15,
                                 headers={'Content-Type': 'application/json'})
            if resp.status_code in (200, 201, 202, 204):
                return "OK"
        except Exception:
            pass

        try:
            text_data = f"{title}\n\n{message}"
            resp = requests.post(CUSTOM_WEBHOOK_URL, data=text_data, timeout=15,
                                 headers={'Content-Type': 'text/plain'})
            if resp.status_code in (200, 201, 202, 204):
                return "OK (text)"
        except Exception:
            pass

        try:
            form_data = {"title": title, "message": message}
            resp = requests.post(CUSTOM_WEBHOOK_URL, data=form_data, timeout=15)
            if resp.status_code in (200, 201, 202, 204):
                return "OK (form)"
        except Exception:
            pass

        return "all formats failed"
    except Exception as e:
        return str(e)


def _send_wechat(title, message):
    payload = {"msgtype": "text", "text": {"content": f"【{title}】\n\n{message[:1500]}"}}
    for attempt in range(3):
        try:
            resp = requests.post(WECHAT_WEBHOOK_URL, json=payload, timeout=15,
                                 headers={'Content-Type': 'application/json'})
            if resp.status_code == 200:
                result = resp.json()
                if result.get("errcode") == 0:
                    return "OK"
                return result.get("errmsg", "failed")
            return f"HTTP {resp.status_code}"
        except Exception as e:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
            else:
                return str(e)
    return "max retries exceeded"


def _send_discord(title, message):
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
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
        return "OK" if resp.status_code in (200, 204) else f"HTTP {resp.status_code}"
    except Exception as e:
        return str(e)


def _send_telegram(title, message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"<b>{title}</b>\n\n{message}",
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        resp = requests.post(url, json=payload, timeout=15)
        return "OK" if resp.status_code == 200 else resp.text
    except Exception as e:
        return str(e)


def _send_feishu(title, message):
    try:
        payload = {"msg_type": "text", "content": {"text": f"{title}\n\n{message}"}}
        resp = requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=15)
        result = resp.json()
        return "OK" if result.get("code") == 0 else result.get("msg", "failed")
    except Exception as e:
        return str(e)


def _send_bark(title, message):
    try:
        body = message.replace("\n", "\\n")[:100]
        url = f"{BARK_URL.rstrip('/')}/{title}/{body}"
        resp = requests.get(url, timeout=15)
        return "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}"
    except Exception as e:
        return str(e)


def _send_pushplus(title, message):
    try:
        url = "https://www.pushplus.plus/send"
        payload = {"token": PUSHPLUS_TOKEN, "title": title, "content": message, "template": "html"}
        resp = requests.post(url, json=payload, timeout=15)
        result = resp.json()
        return "OK" if result.get("code") == 200 else result.get("msg", "failed")
    except Exception as e:
        return str(e)


def _send_serverchan(title, message):
    try:
        url = f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send"
        payload = {"title": title, "desp": message}
        resp = requests.post(url, json=payload, timeout=15)
        result = resp.json()
        return "OK" if result.get("code") == 0 else result.get("message", "failed")
    except Exception as e:
        return str(e)


def send_notification(title: str, message: str, extra_data=None):
    """发送通知到所有已配置的渠道"""
    results = []

    if CUSTOM_WEBHOOK_URL:
        results.append(("自定义Webhook", _send_custom_webhook(title, message, extra_data)))
    if WECHAT_WEBHOOK_URL:
        results.append(("企业微信", _send_wechat(title, message)))
    if DISCORD_WEBHOOK_URL:
        results.append(("Discord", _send_discord(title, message)))
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        results.append(("Telegram", _send_telegram(title, message)))
    if FEISHU_WEBHOOK_URL:
        results.append(("飞书", _send_feishu(title, message)))
    if BARK_URL:
        results.append(("Bark", _send_bark(title, message)))
    if PUSHPLUS_TOKEN:
        results.append(("PushPlus", _send_pushplus(title, message)))
    if SERVER_CHAN_KEY:
        results.append(("Server酱", _send_serverchan(title, message)))

    return results


def get_webhook_status():
    """检查Webhook配置状态"""
    status = []
    checks = [
        (CUSTOM_WEBHOOK_URL, "自定义 Webhook"),
        (WECHAT_WEBHOOK_URL, "企业微信 Webhook"),
        (DISCORD_WEBHOOK_URL, "Discord Webhook"),
        (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, "Telegram Bot"),
        (FEISHU_WEBHOOK_URL, "飞书 Webhook"),
        (BARK_URL, "Bark"),
        (PUSHPLUS_TOKEN, "PushPlus"),
        (SERVER_CHAN_KEY, "Server酱"),
    ]
    for configured, name in checks:
        status.append(f"✅ {name} 已配置" if configured else f"❌ {name} 未配置")
    return status
