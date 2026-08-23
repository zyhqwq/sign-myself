#!/usr/bin/env python3
"""
森空岛签到脚本 - GitHub Actions 专用版 (增强Webhook通知版)
"""

import json
import os
import time
import requests
from datetime import datetime

from skland_common import (
    HEADER, HEADER_LOGIN, HEADER_FOR_SIGN,
    init_did, login, get_sign_header,
    BINDING_URL, ARK_SIGN_URL,
)

# ================== 配置 ==================
TOKEN = os.environ.get('SKLAND_TOKEN', '')
WECHAT_WEBHOOK_URL = os.environ.get('WECHAT_WEBHOOK_URL', '')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_WEBHOOK_URL', '')
BARK_URL = os.environ.get('BARK_URL', '')
PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN', '')
SERVER_CHAN_KEY = os.environ.get('SERVER_CHAN_KEY', '')
CUSTOM_WEBHOOK_URL = os.environ.get('CUSTOM_WEBHOOK_URL', '')

TOKEN_FILE = 'token.json'

# ================== Webhook通知功能 ==================
class NotificationManager:
    """通知管理器，支持多种通知方式"""

    @staticmethod
    def send_all_notifications(subject, message, success_count=0, failed_count=0, total_count=0, detailed_results=None):
        """发送所有配置的通知"""
        results = []

        if CUSTOM_WEBHOOK_URL:
            try:
                result = NotificationManager.send_custom_webhook(subject, message, success_count, failed_count, total_count, detailed_results)
                results.append(("自定义Webhook", result))
            except Exception as e:
                results.append(("自定义Webhook", f"发送失败: {str(e)}"))

        if WECHAT_WEBHOOK_URL:
            try:
                result = NotificationManager.send_wechat_notification(subject, message)
                results.append(("企业微信", result))
            except Exception as e:
                results.append(("企业微信", f"发送失败: {str(e)}"))

        if DISCORD_WEBHOOK_URL:
            try:
                result = NotificationManager.send_discord_notification(subject, message)
                results.append(("Discord", result))
            except Exception as e:
                results.append(("Discord", f"发送失败: {str(e)}"))

        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            try:
                result = NotificationManager.send_telegram_notification(subject, message)
                results.append(("Telegram", result))
            except Exception as e:
                results.append(("Telegram", f"发送失败: {str(e)}"))

        if FEISHU_WEBHOOK_URL:
            try:
                result = NotificationManager.send_feishu_notification(subject, message)
                results.append(("飞书", result))
            except Exception as e:
                results.append(("飞书", f"发送失败: {str(e)}"))

        if BARK_URL:
            try:
                result = NotificationManager.send_bark_notification(subject, message)
                results.append(("Bark", result))
            except Exception as e:
                results.append(("Bark", f"发送失败: {str(e)}"))

        if PUSHPLUS_TOKEN:
            try:
                result = NotificationManager.send_pushplus_notification(subject, message)
                results.append(("PushPlus", result))
            except Exception as e:
                results.append(("PushPlus", f"发送失败: {str(e)}"))

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

        # JSON格式
        try:
            print("  尝试发送JSON格式...")
            response = requests.post(
                CUSTOM_WEBHOOK_URL,
                json=webhook_data,
                timeout=15,
                headers={'Content-Type': 'application/json'}
            )
            print(f"  响应状态码: {response.status_code}")
            print(f"  响应内容: {response.text[:100]}...")
            if response.status_code in [200, 201, 202, 204]:
                return f"✅ JSON格式发送成功 (状态码: {response.status_code})"
        except Exception as e:
            print(f"  JSON格式发送失败: {str(e)}")

        # 纯文本格式
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

        # Form格式
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
        from skland_common import parse_token

        tokens = {}

        if TOKEN:
            token_list = TOKEN.split(',')
            for i, token in enumerate(token_list):
                token = token.strip()
                if token:
                    token_id = f"token_{i+1}"
                    tokens[token_id] = {
                        'token': parse_token(token),
                        'label': token_id,
                        'last_update': time.time(),
                        'login_method': 'github_secret'
                    }

        file_tokens = TokenManager.load_tokens()
        tokens.update(file_tokens)

        return tokens


def get_binding_list(cred_resp):
    """获取绑定的角色列表"""
    try:
        sign_token = cred_resp['token']
        cred = cred_resp['cred']

        current_header = HEADER.copy()
        current_header['cred'] = cred

        final_header = get_sign_header(BINDING_URL, 'get', None, current_header, sign_token)

        response = requests.get(BINDING_URL, headers=final_header, timeout=15)
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
        cred_resp = login(user_token)
        characters = get_binding_list(cred_resp)

        if not characters:
            print("  未找到角色，可能是token失效")
            return {
                'account': account_id,
                'results': ["未找到角色，可能是token失效"],
                'status': 'failed'
            }

        sign_token = cred_resp['token']
        cred = cred_resp['cred']

        current_header = HEADER.copy()
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
                final_header = get_sign_header(
                    ARK_SIGN_URL,
                    'post',
                    body,
                    current_header,
                    sign_token
                )

                response = requests.post(ARK_SIGN_URL, headers=final_header, json=body, timeout=15)
                resp = response.json()

                if resp['code'] == 0:
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

    print("\n📋 Webhook配置状态：")
    webhook_status = NotificationManager.check_webhook_status()
    for status in webhook_status:
        print(f"  {status}")

    if not TOKEN:
        error_msg = "❌ 错误：请在 GitHub Secrets 中设置 SKLAND_TOKEN"
        print(f"\n{error_msg}")
        NotificationManager.send_all_notifications("签到失败", error_msg)
        return

    try:
        init_did()
        print(f"\n✅ 成功生成设备ID")
    except Exception as e:
        error_msg = f"❌ dId 初始化失败：{str(e)}"
        print(f"\n{error_msg}")
        NotificationManager.send_all_notifications("签到失败", error_msg)
        return

    all_tokens = TokenManager.get_all_tokens()

    if not all_tokens:
        error_msg = "❌ 未找到有效token"
        print(f"\n{error_msg}")
        NotificationManager.send_all_notifications("签到失败", error_msg)
        return

    print(f"✅ 找到 {len(all_tokens)} 个账号，开始签到...")

    all_results = []
    success_count = 0
    repeated_count = 0
    failed_count = 0
    total_characters = 0

    for account_id, token_info in all_tokens.items():
        result = do_sign_for_account(account_id, token_info['token'])
        all_results.append(result)

        if result['status'] == 'success':
            success_count += 1
        elif result['status'] == 'repeated':
            repeated_count += 1
        elif result['status'] == 'failed':
            failed_count += 1

        total_characters += result.get('character_count', 0)

    print("\n" + "=" * 50)
    print("签到完成报告")
    print("=" * 50)

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

    max_results_to_show = 2
    for result in all_results:
        status_icon = "✅" if result['status'] == 'success' else "🔄" if result['status'] == 'repeated' else "❌"
        report += f"\n\n{status_icon} 账号: {result['account']}"

        results_to_show = result['results'][:max_results_to_show]
        for res in results_to_show:
            report += f"\n  {res}"

        if len(result['results']) > max_results_to_show:
            report += f"\n  ...（还有{len(result['results']) - max_results_to_show}个结果未显示）"

    if failed_count > 0:
        failed_accounts = [r for r in all_results if r['status'] == 'failed']
        report += f"\n\n❌ 失败账号摘要："
        for fail in failed_accounts[:3]:
            report += f"\n  {fail['account']}: {fail['results'][0] if fail['results'] else '未知错误'}"

    print(report)

    print("\n📨 开始发送通知...")
    notification_results = NotificationManager.send_all_notifications(
        subject,
        report,
        success_count,
        failed_count,
        len(all_results),
        all_results
    )

    if notification_results:
        print("\n📊 通知发送结果：")
        for platform, result in notification_results:
            print(f"  {platform}: {result}")
    else:
        print("ℹ️  未配置任何Webhook，跳过通知")

    if failed_count == len(all_results):
        print("\n❌ 所有账号签到失败")
        exit(1)
    else:
        print("\n✅ 签到任务完成")

if __name__ == "__main__":
    main()
