#!/usr/bin/env python3
"""明日方舟签到脚本 - GitHub Actions 专用版"""

import json
import os
import time
import requests
from datetime import datetime

from notify import send_notification, get_webhook_status, print_notify_results
from skland_common import (
    HEADER, init_did, login, get_sign_header,
    BINDING_URL, ARK_SIGN_URL,
)

TOKEN = os.environ.get('SKLAND_TOKEN', '')
TOKEN_FILE = 'token.json'


class TokenManager:
    """Token管理类"""

    @staticmethod
    def save_tokens(tokens):
        try:
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存token失败：{str(e)}")

    @staticmethod
    def load_tokens():
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
    print("=" * 50)
    print("明日方舟签到脚本")
    print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    print("\n Webhook配置状态：")
    for status in get_webhook_status():
        print(f"  {status}")

    if not TOKEN:
        error_msg = " 错误：请在 GitHub Secrets 中设置 SKLAND_TOKEN"
        print(f"\n{error_msg}")
        print_notify_results(send_notification("签到失败", error_msg))
        exit(1)

    try:
        init_did()
        print(f"\n 成功生成设备ID")
    except Exception as e:
        import traceback
        error_msg = f" dId 初始化失败：{str(e)}"
        print(f"\n{error_msg}")
        print(f"\n详细错误信息：\n{traceback.format_exc()}")
        print_notify_results(send_notification("签到失败", error_msg))
        exit(1)

    all_tokens = TokenManager.get_all_tokens()

    if not all_tokens:
        error_msg = " 未找到有效token"
        print(f"\n{error_msg}")
        print_notify_results(send_notification("签到失败", error_msg))
        exit(1)

    print(f" 找到 {len(all_tokens)} 个账号，开始签到...")

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
    elif repeated_count > 0:
        subject = f"重复签到 ({repeated_count}个重复)"
    elif failed_count > 0:
        subject = f"签到失败 ({failed_count}个失败)"
    else:
        subject = "签到完成"

    report = f"""签到统计：
{subject}
• 账号总数: {len(all_results)}
• 签到成功: {success_count}
• 重复签到: {repeated_count}
• 签到失败: {failed_count}
• 角色总数: {total_characters}

详细结果："""

    max_results_to_show = 2
    for result in all_results:
        report += f"\n\n账号: {result['account']}"

        results_to_show = result['results'][:max_results_to_show]
        for res in results_to_show:
            report += f"\n  {res}"

        if len(result['results']) > max_results_to_show:
            report += f"\n  ...（还有{len(result['results']) - max_results_to_show}个结果未显示）"

    if failed_count > 0:
        failed_accounts = [r for r in all_results if r['status'] == 'failed']
        report += f"\n\n 失败账号摘要："
        for fail in failed_accounts[:3]:
            report += f"\n  {fail['account']}: {fail['results'][0] if fail['results'] else '未知错误'}"

    print(report)

    print("\n 开始发送通知...")
    print_notify_results(send_notification(subject, report))

    if failed_count == len(all_results):
        print("\n 所有账号签到失败")
        exit(1)
    else:
        print("\n 签到任务完成")


if __name__ == "__main__":
    main()
