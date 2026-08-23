#!/usr/bin/env python3
"""共享通知模块 - 支持多种通知渠道"""

import os
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


def send_notification(title: str, message: str):
    """发送通知到所有已配置的渠道"""
    results = []

    if CUSTOM_WEBHOOK_URL:
        results.append(("自定义Webhook", _send_custom_webhook(title, message)))
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


def _send_custom_webhook(title, message):
    try:
        data = {
            "event": "daily_sign",
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "source": "github_actions",
        }
        resp = requests.post(CUSTOM_WEBHOOK_URL, json=data, timeout=15,
                             headers={'Content-Type': 'application/json'})
        if resp.status_code in (200, 201, 202, 204):
            return "OK"
        return f"HTTP {resp.status_code}"
    except Exception as e:
        return str(e)


def _send_wechat(title, message):
    try:
        payload = {"msgtype": "text", "text": {"content": f"【{title}】\n\n{message[:1500]}"}}
        resp = requests.post(WECHAT_WEBHOOK_URL, json=payload, timeout=15,
                             headers={'Content-Type': 'application/json'})
        if resp.status_code == 200 and resp.json().get("errcode") == 0:
            return "OK"
        return resp.json().get("errmsg", "failed")
    except Exception as e:
        return str(e)


def _send_discord(title, message):
    try:
        payload = {
            "content": f"**{title}**\n\n{message}"[:2000],
            "embeds": [{"title": title, "description": message[:2000],
                        "timestamp": datetime.now().isoformat()}]
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
