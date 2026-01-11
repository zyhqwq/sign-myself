#!/usr/bin/env python3
"""
森空岛签到脚本 - GitHub Actions 专用版 (增强Webhook通知版)
"""

import hashlib
import hmac
import json
import logging
import os
import time
import random
import uuid
import base64
import gzip
import requests
from datetime import datetime, timedelta
from urllib import parse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.base import Cipher
from cryptography.hazmat.primitives.ciphers.modes import ECB, CBC

# ================== 配置 ==================
TOKEN = os.environ.get('SKLAND_TOKEN', '')  # GitHub Secrets 中的 token
WECHAT_WEBHOOK_URL = os.environ.get('WECHAT_WEBHOOK_URL', '')  # 企业微信 Webhook
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')  # Discord Webhook
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')  # Telegram Bot Token
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')  # Telegram Chat ID
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_WEBHOOK_URL', '')  # 飞书 Webhook
BARK_URL = os.environ.get('BARK_URL', '')  # Bark 通知 URL
PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN', '')  # PushPlus Token
SERVER_CHAN_KEY = os.environ.get('SERVER_CHAN_KEY', '')  # Server酱 KEY
CUSTOM_WEBHOOK_URL = os.environ.get('CUSTOM_WEBHOOK_URL', '')  # 你的自定义 Webhook URL

TOKEN_FILE = 'token.json'  # 保存 token 的文件

# ================== 数美配置 ==================
SM_CONFIG = {
    "organization": "UWXspnCCJN4sfYlNfqps",
    "appId": "default",
    "publicKey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmxMNr7n8ZeT0tE1R9j/mPixoinPkeM+k4VGIn/s0k7N5rJAfnZ0eMER+QhwFvshzo0LNmeUkpR8uIlU/GEVr8mN28sKmwd2gpygqj0ePnBmOW4v0ZVwbSYK+izkhVFk2V/doLoMbWy6b+UnA8mkjvg0iYWRByfRsK2gdl7llqCwIDAQAB",
    "protocol": "https",
    "apiHost": "fp-it.portal101.cn"
}

# 加载数美公钥
PK = serialization.load_der_public_key(base64.b64decode(SM_CONFIG['publicKey']))

# 其他配置
app_code = '4ca99fa6b56cc2ba'

# ================== 请求头 ==================
header = {
    'cred': '',
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close'
}

header_login = {
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close',
    'dId': ''
}

header_for_sign = {
    'platform': '',
    'timestamp': '',
    'dId': '',
    'vName': ''
}

# 接口URL
sign_url = "https://zonai.skland.com/api/v1/game/attendance"
binding_url = "https://zonai.skland.com/api/v1/game/player/binding"
grant_code_url = "https://as.hypergryph.com/user/oauth2/v2/grant"
cred_code_url = "https://zonai.skland.com/web/v1/user/auth/generate_cred_by_code"

# ================== 数美设备ID生成 ==================
devices_info_url = "https://fp-it.portal101.cn/deviceprofile/v4"

# 模拟浏览器环境参数
BROWSER_ENV = {
    'plugins': 'MicrosoftEdgePDFPluginPortableDocumentFormatinternal-pdf-viewer1,MicrosoftEdgePDFViewermhjfbmdgcfjbbpaeojofohoefgiehjai1',
    'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
    'canvas': '259ffe69',
    'timezone': -480,
    'platform': 'Win32',
    'url': 'https://www.skland.com/',
    'referer': '',
    'res': '1920_1080_24_1.25',
    'clientSize': '0_0_1080_1920_1920_1080',
    'status': '0011',
}

# DES加密规则
DES_RULE = {
    "appId": {"cipher": "DES", "is_encrypt": 1, "key": "uy7mzc4h", "obfuscated_name": "xx"},
    "box": {"is_encrypt": 0, "obfuscated_name": "jf"},
    "canvas": {"cipher": "DES", "is_encrypt": 1, "key": "snrn887t", "obfuscated_name": "yk"},
    "clientSize": {"cipher": "DES", "is_encrypt": 1, "key": "cpmjjgsu", "obfuscated_name": "zx"},
    "organization": {"cipher": "DES", "is_encrypt": 1, "key": "78moqjfc", "obfuscated_name": "dp"},
    "os": {"cipher": "DES", "is_encrypt": 1, "key": "je6vk6t4", "obfuscated_name": "pj"},
    "platform": {"cipher": "DES", "is_encrypt": 1, "key": "pakxhcd2", "obfuscated_name": "gm"},
    "plugins": {"cipher": "DES", "is_encrypt": 1, "key": "v51m3pzl", "obfuscated_name": "kq"},
    "pmf": {"cipher": "DES", "is_encrypt": 1, "key": "2mdeslu3", "obfuscated_name": "vw"},
    "protocol": {"is_encrypt": 0, "obfuscated_name": "protocol"},
    "referer": {"cipher": "DES", "is_encrypt": 1, "key": "y7bmrjlc", "obfuscated_name": "ab"},
    "res": {"cipher": "DES", "is_encrypt": 1, "key": "whxqm2a7", "obfuscated_name": "hf"},
    "rtype": {"cipher": "DES", "is_encrypt": 1, "key": "x8o2h2bl", "obfuscated_name": "lo"},
    "sdkver": {"cipher": "DES", "is_encrypt": 1, "key": "9q3dcxp2", "obfuscated_name": "sc"},
    "status": {"cipher": "DES", "is_encrypt": 1, "key": "2jbrxxw4", "obfuscated_name": "an"},
    "subVersion": {"cipher": "DES", "is_encrypt": 1, "key": "eo3i2puh", "obfuscated_name": "ns"},
    "svm": {"cipher": "DES", "is_encrypt": 1, "key": "fzj3kaeh", "obfuscated_name": "qr"},
    "time": {"cipher": "DES", "is_encrypt": 1, "key": "q2t3odsk", "obfuscated_name": "nb"},
    "timezone": {"cipher": "DES", "is_encrypt": 1, "key": "1uv05lj5", "obfuscated_name": "as"},
    "tn": {"cipher": "DES", "is_encrypt": 1, "key": "x9nzj1bp", "obfuscated_name": "py"},
    "trees": {"cipher": "DES", "is_encrypt": 1, "key": "acfs0xo4", "obfuscated_name": "pi"},
    "ua": {"cipher": "DES", "is_encrypt": 1, "key": "k92crp1t", "obfuscated_name": "bj"},
    "url": {"cipher": "DES", "is_encrypt": 1, "key": "y95hjkoo", "obfuscated_name": "cf"},
    "version": {"is_encrypt": 0, "obfuscated_name": "version"},
    "vpw": {"cipher": "DES", "is_encrypt": 1, "key": "r9924ab5", "obfuscated_name": "ca"}
}

# ================== 加密函数 ==================
def _des_encrypt_ecb(data: bytes, key: str):
    """DES ECB模式加密"""
    key_bytes = key.encode('utf-8')
    
    if len(key_bytes) < 8:
        key_bytes = key_bytes.ljust(8, b'\x00')
    elif len(key_bytes) > 8:
        key_bytes = key_bytes[:8]
    
    try:
        from cryptography.hazmat.primitives.ciphers.algorithms import TripleDES
        triple_key = key_bytes * 3
        cipher = Cipher(TripleDES(triple_key), ECB())
        encryptor = cipher.encryptor()
        
        padding_len = 8 - (len(data) % 8)
        if padding_len != 8:
            data += b'\x00' * padding_len
        
        encrypted = encryptor.update(data) + encryptor.finalize()
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"DES加密失败: {str(e)}")
        return base64.b64encode(data).decode('utf-8')

def _DES(o: dict):
    """对字段进行DES加密处理"""
    result = {}
    for i in o.keys():
        if i in DES_RULE:
            rule = DES_RULE[i]
            res = o[i]
            if rule['is_encrypt'] == 1:
                data = str(res).encode('utf-8')
                res = _des_encrypt_ecb(data, rule['key'])
            result[rule['obfuscated_name']] = res
        else:
            result[i] = o[i]
    return result

def _AES(v: bytes, k: bytes):
    """AES-CBC加密"""
    iv = '0102030405060708'
    cipher = Cipher(AES(k), CBC(iv.encode('utf-8')))
    v += b'\x00'
    while len(v) % 16 != 0:
        v += b'\x00'
    return cipher.encryptor().update(v).hex()

def GZIP(o: dict):
    """GZIP压缩并Base64编码"""
    json_str = json.dumps(o, ensure_ascii=False)
    compressed = gzip.compress(json_str.encode('utf-8'), 2, mtime=0)
    return base64.b64encode(compressed)

def get_tn(o: dict):
    """生成tn参数（用于加密）"""
    sorted_keys = sorted(o.keys())
    result_list = []
    for key in sorted_keys:
        val = o[key]
        if isinstance(val, (int, float)):
            val = str(val * 10000)
        elif isinstance(val, dict):
            val = get_tn(val)
        result_list.append(val)
    return ''.join(result_list)

def get_smid():
    """生成smid参数"""
    t = time.localtime()
    _time = f'{t.tm_year}{t.tm_mon:02d}{t.tm_mday:02d}{t.tm_hour:02d}{t.tm_min:02d}{t.tm_sec:02d}'
    uid = str(uuid.uuid4())
    md5_uid = hashlib.md5(uid.encode('utf-8')).hexdigest()
    smsk_web = hashlib.md5(f'smsk_web_{_time}{md5_uid}00'.encode('utf-8')).hexdigest()[:14]
    return f'{_time}{md5_uid}00{smsk_web}0'

def get_d_id():
    """生成dId参数（数美设备ID）"""
    uid = str(uuid.uuid4()).encode('utf-8')
    priId = hashlib.md5(uid).hexdigest()[:16]
    
    # RSA加密uid
    ep = PK.encrypt(uid, padding.PKCS1v15())
    ep = base64.b64encode(ep).decode('utf-8')

    # 构建浏览器环境参数
    browser = BROWSER_ENV.copy()
    current_time = int(time.time() * 1000)
    browser.update({
        'vpw': str(uuid.uuid4()),
        'svm': current_time,
        'trees': str(uuid.uuid4()),
        'pmf': current_time
    })

    # 构建待加密数据
    des_target = {
        **browser,
        'protocol': 102,
        'organization': SM_CONFIG['organization'],
        'appId': SM_CONFIG['appId'],
        'os': 'web',
        'version': '3.0.0',
        'sdkver': '3.0.0',
        'box': '',
        'rtype': 'all',
        'smid': get_smid(),
        'subVersion': '1.0.0',
        'time': 0
    }
    des_target['tn'] = hashlib.md5(get_tn(des_target).encode()).hexdigest()

    # 加密流程
    des_result = _AES(GZIP(_DES(des_target)), priId.encode('utf-8'))

    # 请求数美接口
    try:
        response = requests.post(
            devices_info_url,
            json={
                'appId': 'default',
                'compress': 2,
                'data': des_result,
                'encode': 5,
                'ep': ep,
                'organization': SM_CONFIG['organization'],
                'os': 'web'
            },
            timeout=15
        )
        response.raise_for_status()
        resp = response.json()
    except Exception as e:
        raise Exception(f"数美接口请求失败：{str(e)}")
        
    if resp['code'] != 1100:
        raise Exception(f"dId生成失败，错误码：{resp['code']}")
    return 'B' + resp['detail']['deviceId']

# ================== Webhook通知功能 ==================
class NotificationManager:
    """通知管理器，支持多种通知方式"""
    
    @staticmethod
    def send_all_notifications(subject, message, success_count=0, failed_count=0, total_count=0, detailed_results=None):
        """发送所有配置的通知"""
        results = []
        
        # 自定义Webhook
        if CUSTOM_WEBHOOK_URL:
            try:
                result = NotificationManager.send_custom_webhook(subject, message, success_count, failed_count, total_count, detailed_results)
                results.append(("自定义Webhook", result))
            except Exception as e:
                results.append(("自定义Webhook", f"发送失败: {str(e)}"))
        
        # 企业微信
        if WECHAT_WEBHOOK_URL:
            try:
                result = NotificationManager.send_wechat_notification(subject, message)
                results.append(("企业微信", result))
            except Exception as e:
                results.append(("企业微信", f"发送失败: {str(e)}"))
        
        # Discord
        if DISCORD_WEBHOOK_URL:
            try:
                result = NotificationManager.send_discord_notification(subject, message)
                results.append(("Discord", result))
            except Exception as e:
                results.append(("Discord", f"发送失败: {str(e)}"))
        
        # Telegram
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            try:
                result = NotificationManager.send_telegram_notification(subject, message)
                results.append(("Telegram", result))
            except Exception as e:
                results.append(("Telegram", f"发送失败: {str(e)}"))
        
        # 飞书
        if FEISHU_WEBHOOK_URL:
            try:
                result = NotificationManager.send_feishu_notification(subject, message)
                results.append(("飞书", result))
            except Exception as e:
                results.append(("飞书", f"发送失败: {str(e)}"))
        
        # Bark
        if BARK_URL:
            try:
                result = NotificationManager.send_bark_notification(subject, message)
                results.append(("Bark", result))
            except Exception as e:
                results.append(("Bark", f"发送失败: {str(e)}"))
        
        # PushPlus
        if PUSHPLUS_TOKEN:
            try:
                result = NotificationManager.send_pushplus_notification(subject, message)
                results.append(("PushPlus", result))
            except Exception as e:
                results.append(("PushPlus", f"发送失败: {str(e)}"))
        
        # Server酱
        if SERVER_CHAN_KEY:
            try:
                result = NotificationManager.send_serverchan_notification(subject, message)
                results.append(("Server酱", result))
            except Exception as e:
                results.append(("Server酱", f"发送失败: {str(e)}"))
        
        return results
    
    @staticmethod
    def send_custom_webhook(subject, message, success_count, failed_count, total_count, detailed_results=None):
        """发送到自定义Webhook"""
        print(f"\n📤 尝试发送到自定义Webhook: {CUSTOM_WEBHOOK_URL}")
        
        # 构建详细的JSON数据
        webhook_data = {
            "event": "skland_sign",
            "timestamp": datetime.now().isoformat(),
            "success": success_count > 0,
            "summary": {
                "total_accounts": total_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "subject": subject,
                "message": message
            },
            "detailed_results": detailed_results if detailed_results else [],
            "source": "github_actions",
            "action_id": os.environ.get('GITHUB_RUN_ID', 'unknown'),
            "repository": os.environ.get('GITHUB_REPOSITORY', 'unknown')
        }
        
        # 尝试多种格式发送
        
        # 格式1: JSON格式（推荐）
        try:
            print("  尝试发送JSON格式...")
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                CUSTOM_WEBHOOK_URL,
                json=webhook_data,
                timeout=15,
                headers=headers
            )
            
            print(f"  响应状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:100]}...")
            
            if response.status_code in [200, 201, 202, 204]:
                return f"✅ JSON格式发送成功 (状态码: {response.status_code})"
        except Exception as e:
            print(f"  JSON格式发送失败: {str(e)}")
        
        # 格式2: 纯文本格式（备用）
        try:
            print("  尝试发送纯文本格式...")
            text_data = f"森空岛签到\n{subject}\n\n{message}"
            response = requests.post(
                CUSTOM_WEBHOOK_URL,
                data=text_data,
                timeout=15,
                headers={'Content-Type': 'text/plain'}
            )
            
            print(f"  响应状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:100]}...")
            
            if response.status_code in [200, 201, 202, 204]:
                return f"✅ 纯文本格式发送成功 (状态码: {response.status_code})"
        except Exception as e:
            print(f"  纯文本格式发送失败: {str(e)}")
        
        # 格式3: Form格式（备用）
        try:
            print("  尝试发送Form格式...")
            form_data = {
                "subject": subject,
                "message": message,
                "success_count": str(success_count),
                "failed_count": str(failed_count),
                "total_count": str(total_count)
            }
            response = requests.post(
                CUSTOM_WEBHOOK_URL,
                data=form_data,
                timeout=15
            )
            
            print(f"  响应状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:100]}...")
            
            if response.status_code in [200, 201, 202, 204]:
                return f"✅ Form格式发送成功 (状态码: {response.status_code})"
        except Exception as e:
            print(f"  Form格式发送失败: {str(e)}")
        
        return "❌ 所有格式尝试均失败"
    
    @staticmethod
    def send_wechat_notification(subject, message, max_retries=3):
        """发送企业微信通知"""
        payload = {
            "msgtype": "text",
            "text": {
                "content": f"【森空岛签到】{subject}\n\n{message[:1500]}"
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    WECHAT_WEBHOOK_URL, 
                    json=payload, 
                    timeout=15,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("errcode") == 0:
                        return "✅ 发送成功"
                    else:
                        return f"❌ 发送失败: {result.get('errmsg', '未知错误')}"
                else:
                    return f"❌ HTTP错误: {response.status_code}"
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    return f"❌ 请求异常: {str(e)}"
        
        return "❌ 发送失败，已达最大重试次数"
    
    @staticmethod
    def send_discord_notification(subject, message):
        """发送Discord通知"""
        content = f"## 森空岛签到\n**{subject}**\n\n{message}"
        
        payload = {
            "content": content[:2000],
            "embeds": [{
                "title": subject,
                "description": message[:2000],
                "color": 3066993 if "成功" in subject else 15158332 if "失败" in subject else 16776960,
                "timestamp": datetime.now().isoformat()
            }]
        }
        
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
            return "✅ 发送成功" if response.status_code in [200, 204] else f"❌ 发送失败: {response.status_code}"
        except Exception as e:
            return f"❌ 请求异常: {str(e)}"
    
    @staticmethod
    def send_telegram_notification(subject, message):
        """发送Telegram通知"""
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        html_message = f"<b>森空岛签到</b>\n<b>{subject}</b>\n\n{message}"
        html_message = html_message.replace("\n", "\n")
        
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': html_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                return "✅ 发送成功"
            else:
                return f"❌ 发送失败: {response.text}"
        except Exception as e:
            return f"❌ 请求异常: {str(e)}"
    
    @staticmethod
    def send_feishu_notification(subject, message):
        """发送飞书通知"""
        payload = {
            "msg_type": "text",
            "content": {
                "text": f"森空岛签到\n{subject}\n\n{message}"
            }
        }
        
        try:
            response = requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=15)
            result = response.json()
            return "✅ 发送成功" if result.get("code") == 0 else f"❌ 发送失败: {result.get('msg', '未知错误')}"
        except Exception as e:
            return f"❌ 请求异常: {str(e)}"
    
    @staticmethod
    def send_bark_notification(subject, message):
        """发送Bark通知"""
        title = f"森空岛签到 - {subject}"
        body = message.replace("\n", "\\n")[:100]
        
        bark_url = f"{BARK_URL.rstrip('/')}/{title}/{body}"
        
        try:
            response = requests.get(bark_url, timeout=15)
            return "✅ 发送成功" if response.status_code == 200 else f"❌ 发送失败: {response.status_code}"
        except Exception as e:
            return f"❌ 请求异常: {str(e)}"
    
    @staticmethod
    def send_pushplus_notification(subject, message):
        """发送PushPlus通知"""
        url = "https://www.pushplus.plus/send"
        
        payload = {
            "token": PUSHPLUS_TOKEN,
            "title": f"森空岛签到 - {subject}",
            "content": message,
            "template": "html"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            result = response.json()
            return "✅ 发送成功" if result.get("code") == 200 else f"❌ 发送失败: {result.get('msg', '未知错误')}"
        except Exception as e:
            return f"❌ 请求异常: {str(e)}"
    
    @staticmethod
    def send_serverchan_notification(subject, message):
        """发送Server酱通知"""
        url = f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send"
        
        payload = {
            "title": f"森空岛签到 - {subject}",
            "desp": message
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            result = response.json()
            return "✅ 发送成功" if result.get("code") == 0 else f"❌ 发送失败: {result.get('message', '未知错误')}"
        except Exception as e:
            return f"❌ 请求异常: {str(e)}"
    
    @staticmethod
    def check_webhook_status():
        """检查Webhook配置状态"""
        status = []
        
        if CUSTOM_WEBHOOK_URL:
            status.append("✅ 自定义 Webhook 已配置")
        else:
            status.append("❌ 自定义 Webhook 未配置")
            
        if WECHAT_WEBHOOK_URL:
            status.append("✅ 企业微信 Webhook 已配置")
        else:
            status.append("❌ 企业微信 Webhook 未配置")
            
        if DISCORD_WEBHOOK_URL:
            status.append("✅ Discord Webhook 已配置")
        else:
            status.append("❌ Discord Webhook 未配置")
            
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            status.append("✅ Telegram Bot 已配置")
        else:
            status.append("❌ Telegram Bot 未配置")
            
        if FEISHU_WEBHOOK_URL:
            status.append("✅ 飞书 Webhook 已配置")
        else:
            status.append("❌ 飞书 Webhook 未配置")
            
        if BARK_URL:
            status.append("✅ Bark 已配置")
        else:
            status.append("❌ Bark 未配置")
            
        if PUSHPLUS_TOKEN:
            status.append("✅ PushPlus 已配置")
        else:
            status.append("❌ PushPlus 未配置")
            
        if SERVER_CHAN_KEY:
            status.append("✅ Server酱 已配置")
        else:
            status.append("❌ Server酱 未配置")
        
        return status

# ================== 签到核心功能 ==================
class TokenManager:
    """Token管理类"""
    
    @staticmethod
    def parse_token(token_str):
        """解析token字符串"""
        try:
            data = json.loads(token_str)
            if 'data' in data and 'content' in data['data']:
                return data['data']['content']
        except:
            pass
        return token_str
    
    @staticmethod
    def save_tokens(tokens):
        """保存token到文件"""
        try:
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存token失败：{str(e)}")
    
    @staticmethod
    def load_tokens():
        """从文件加载token"""
        if not os.path.exists(TOKEN_FILE):
            return {}
        
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载token失败：{str(e)}")
            return {}
    
    @staticmethod
    def get_all_tokens():
        """获取所有token（从环境变量和文件）"""
        tokens = {}
        
        # 从环境变量获取
        if TOKEN:
            token_list = TOKEN.split(',')
            for i, token in enumerate(token_list):
                token = token.strip()
                if token:
                    token_id = f"token_{i+1}"
                    tokens[token_id] = {
                        'token': TokenManager.parse_token(token),
                        'label': token_id,
                        'last_update': time.time(),
                        'login_method': 'github_secret'
                    }
        
        # 从文件获取（如果有）
        file_tokens = TokenManager.load_tokens()
        tokens.update(file_tokens)
        
        return tokens

def generate_signature(token: str, path, body_or_query):
    """生成签名（HMAC-SHA256 + MD5）"""
    t = str(int(time.time()) - 2)
    token = token.encode('utf-8')
    header_ca = json.loads(json.dumps(header_for_sign))
    header_ca['timestamp'] = t
    header_ca_str = json.dumps(header_ca, separators=(',', ':'))
    s = path + body_or_query + t + header_ca_str
    try:
        hex_s = hmac.new(token, s.encode('utf-8'), hashlib.sha256).hexdigest()
        md5 = hashlib.md5(hex_s.encode('utf-8')).hexdigest()
        return md5, header_ca
    except Exception as e:
        raise Exception(f"签名生成失败：{str(e)}")

def get_sign_header(url: str, method, body, h, token):
    """构建带签名的请求头"""
    p = parse.urlparse(url)
    if method.lower() == 'get':
        h['sign'], header_ca = generate_signature(token, p.path, p.query)
    else:
        h['sign'], header_ca = generate_signature(token, p.path, json.dumps(body) if body else '')
    for i in header_ca:
        h[i] = header_ca[i]
    return h

def get_grant_code(token):
    """获取认证代码"""
    try:
        response = requests.post(grant_code_url, json={
            'appCode': app_code,
            'token': token,
            'type': 0
        }, headers=header_login, timeout=10)
        resp = response.json()
        if response.status_code != 200 or resp.get('status') != 0:
            raise Exception(f'获取认证代码失败：{resp.get("msg", "未知错误")}')
        return resp['data']['code']
    except Exception as e:
        raise Exception(f"网络请求失败：{str(e)}")

def get_cred(grant):
    """通过认证代码获取cred"""
    try:
        resp = requests.post(cred_code_url, json={
            'code': grant,
            'kind': 1
        }, headers=header_login, timeout=10).json()
        if resp['code'] != 0:
            raise Exception(f'获取cred失败：{resp["message"]}')
        return resp['data']
    except Exception as e:
        raise Exception(f"获取cred失败：{str(e)}")

def get_binding_list(cred_resp):
    """获取绑定的角色列表"""
    try:
        sign_token = cred_resp['token']
        cred = cred_resp['cred']
        
        # 准备请求头
        current_header = header.copy()
        current_header['cred'] = cred
        
        # 生成签名
        final_header = get_sign_header(
            binding_url, 
            'get', 
            None, 
            current_header, 
            sign_token
        )
        
        # 发送请求
        response = requests.get(binding_url, headers=final_header, timeout=15)
        resp = response.json()
        
        if resp['code'] != 0:
            print(f"角色列表请求失败：{resp['message']}")
            return []
        
        v = []
        for i in resp['data']['list']:
            if i.get('appCode') == 'arknights':
                v.extend(i.get('bindingList', []))
        return v
    except Exception as e:
        print(f"获取角色列表失败：{str(e)}")
        return []

def do_sign_for_account(account_id, user_token):
    """为单个账号执行签到"""
    print(f"\n处理账号: {account_id}")
    
    try:
        # 获取凭证
        grant_code = get_grant_code(user_token)
        cred_resp = get_cred(grant_code)
        
        # 获取角色列表
        characters = get_binding_list(cred_resp)
        
        if not characters:
            print("  未找到角色，可能是token失效")
            return {
                'account': account_id,
                'results': ["未找到角色，可能是token失效"],
                'status': 'failed'
            }
        
        # 准备签到请求头
        sign_token = cred_resp['token']
        cred = cred_resp['cred']
        
        current_header = header.copy()
        current_header['cred'] = cred
        
        results = []
        status_list = []
        
        for character in characters:
            character_name = character.get("nickName", "未知角色")
            uid = character.get('uid', '')
            
            if not uid:
                continue
                
            body = {'gameId': 1, 'uid': uid}
            
            try:
                # 生成签名
                final_header = get_sign_header(
                    sign_url,
                    'post',
                    body,
                    current_header,
                    sign_token
                )
                
                # 发送签到请求
                response = requests.post(sign_url, headers=final_header, json=body, timeout=15)
                resp = response.json()
                
                if resp['code'] == 0:
                    # 签到成功
                    awards = resp['data']['awards']
                    award_info = []
                    for award in awards:
                        res = award['resource']
                        award_info.append(f"{res['name']}×{award.get('count', 1)}")
                    
                    result_msg = f"角色 {character_name} 签到成功，获得: {', '.join(award_info)}"
                    results.append(result_msg)
                    status_list.append('success')
                    
                elif resp.get('code') == 10001 and '请勿重复签到' in resp.get('message', ''):
                    result_msg = f"角色 {character_name} 今天已经签到过了！"
                    results.append(result_msg)
                    status_list.append('repeated')
                    
                elif resp.get('message') == '请勿重复签到':
                    result_msg = f"角色 {character_name} 今天已经签到过了！"
                    results.append(result_msg)
                    status_list.append('repeated')
                    
                else:
                    result_msg = f"角色 {character_name} 签到失败：{resp.get('message', '未知错误')}"
                    results.append(result_msg)
                    status_list.append('failed')
                    
            except Exception as e:
                result_msg = f"角色 {character_name} 签到异常：{str(e)}"
                results.append(result_msg)
                status_list.append('failed')
        
        # 确定整体状态
        if 'success' in status_list:
            overall_status = 'success'
        elif 'failed' in status_list:
            overall_status = 'failed'
        else:
            overall_status = 'repeated'
            
        return {
            'account': account_id,
            'results': results,
            'status': overall_status,
            'character_count': len(characters)
        }
        
    except Exception as e:
        error_msg = f"签到失败：{str(e)}"
        print(f"  {error_msg}")
        return {
            'account': account_id,
            'results': [error_msg],
            'status': 'failed',
            'character_count': 0
        }

def main():
    """主函数"""
    print("=" * 50)
    print("森空岛签到脚本 - 增强Webhook通知版")
    print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 检查Webhook配置状态
    print("\n📋 Webhook配置状态：")
    webhook_status = NotificationManager.check_webhook_status()
    for status in webhook_status:
        print(f"  {status}")
    
    # 检查是否有token
    if not TOKEN:
        error_msg = "❌ 错误：请在 GitHub Secrets 中设置 SKLAND_TOKEN"
        print(f"\n{error_msg}")
        NotificationManager.send_all_notifications("签到失败", error_msg)
        return
    
    # 初始化 dId
    try:
        d_id = get_d_id()
        header_login['dId'] = d_id
        header_for_sign['dId'] = d_id
        print(f"\n✅ 成功生成设备ID")
    except Exception as e:
        error_msg = f"❌ dId 初始化失败：{str(e)}"
        print(f"\n{error_msg}")
        NotificationManager.send_all_notifications("签到失败", error_msg)
        return
    
    # 获取所有token
    all_tokens = TokenManager.get_all_tokens()
    
    if not all_tokens:
        error_msg = "❌ 未找到有效token"
        print(f"\n{error_msg}")
        NotificationManager.send_all_notifications("签到失败", error_msg)
        return
    
    print(f"✅ 找到 {len(all_tokens)} 个账号，开始签到...")
    
    # 执行签到
    all_results = []
    success_count = 0
    repeated_count = 0
    failed_count = 0
    total_characters = 0
    
    for account_id, token_info in all_tokens.items():
        result = do_sign_for_account(account_id, token_info['token'])
        all_results.append(result)
        
        # 更新统计
        if result['status'] == 'success':
            success_count += 1
        elif result['status'] == 'repeated':
            repeated_count += 1
        elif result['status'] == 'failed':
            failed_count += 1
        
        total_characters += result.get('character_count', 0)
    
    # 生成报告
    print("\n" + "=" * 50)
    print("签到完成报告")
    print("=" * 50)
    
    # 构建通知消息
    if success_count > 0:
        subject = f"签到成功 ({success_count}个成功)"
        emoji = "✅"
    elif repeated_count > 0:
        subject = f"重复签到 ({repeated_count}个重复)"
        emoji = "🔄"
    elif failed_count > 0:
        subject = f"签到失败 ({failed_count}个失败)"
        emoji = "❌"
    else:
        subject = "签到完成"
        emoji = "📝"
    
    report = f"""📊 签到统计：
{emoji} {subject}
• 账号总数: {len(all_results)}
• 签到成功: {success_count}
• 重复签到: {repeated_count}
• 签到失败: {failed_count}
• 角色总数: {total_characters}

📋 详细结果："""

    # 限制详细结果长度
    max_results_to_show = 2
    for result in all_results:
        status_icon = "✅" if result['status'] == 'success' else "🔄" if result['status'] == 'repeated' else "❌"
        report += f"\n\n{status_icon} 账号: {result['account']}"
        
        results_to_show = result['results'][:max_results_to_show]
        for res in results_to_show:
            report += f"\n  {res}"
        
        if len(result['results']) > max_results_to_show:
            report += f"\n  ...（还有{len(result['results']) - max_results_to_show}个结果未显示）"
    
    # 添加失败摘要
    if failed_count > 0:
        failed_accounts = [r for r in all_results if r['status'] == 'failed']
        report += f"\n\n❌ 失败账号摘要："
        for fail in failed_accounts[:3]:  # 最多显示3个失败账号
            report += f"\n  {fail['account']}: {fail['results'][0] if fail['results'] else '未知错误'}"
    
    print(report)
    
    # 发送通知
    print("\n📨 开始发送通知...")
    notification_results = NotificationManager.send_all_notifications(
        subject, 
        report,
        success_count,
        failed_count,
        len(all_results),
        all_results  # 传递详细结果给自定义webhook
    )
    
    # 显示通知发送结果
    if notification_results:
        print("\n📊 通知发送结果：")
        for platform, result in notification_results:
            print(f"  {platform}: {result}")
    else:
        print("ℹ️  未配置任何Webhook，跳过通知")
    
    # 如果全部失败，退出码设为1（让GitHub Actions标记为失败）
    if failed_count == len(all_results):
        print("\n❌ 所有账号签到失败")
        exit(1)
    else:
        print("\n✅ 签到任务完成")

if __name__ == "__main__":
    main()