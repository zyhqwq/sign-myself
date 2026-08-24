#!/usr/bin/env python3
"""明日方舟：终末地 签到脚本 - GitHub Actions 专用版"""

import json
import os
import sys
import requests
from datetime import datetime

from notify import send_notification, print_notify_results, format_sign_entry
from skland_common import (
    HEADER, init_did, login, get_sign_header,
    BINDING_URL, ENDFIELD_SIGN_URL,
)

TOKEN = os.environ.get('SKLAND_TOKEN', '')


def get_endfield_characters(cred_resp):
    sign_token = cred_resp['token']
    cred = cred_resp['cred']

    current_header = HEADER.copy()
    current_header['cred'] = cred

    final_header = get_sign_header(BINDING_URL, 'get', None, current_header, sign_token)
    response = requests.get(BINDING_URL, headers=final_header, timeout=15)
    resp = response.json()

    if resp['code'] != 0:
        raise Exception(f"获取角色列表失败：{resp['message']}")

    characters = []
    for entry in resp['data']['list']:
        if entry.get('appCode') == 'endfield':
            for char in entry.get('bindingList', []):
                default_role = char.get('defaultRole') or {}
                roles = char.get('roles', [])
                role = default_role or (roles[0] if roles else {})
                characters.append({
                    'roleId': role.get('roleId', ''),
                    'nickName': role.get('nickname', '') or char.get('nickName', '') or '未知角色',
                    'serverId': role.get('serverId', char.get('channelMasterId', '')),
                    'level': role.get('level', 0),
                })
    return characters


def do_endfield_sign(sign_token, cred, role_id, server_id):
    current_header = HEADER.copy()
    current_header['cred'] = cred

    final_header = get_sign_header(ENDFIELD_SIGN_URL, 'post', None, current_header, sign_token)
    final_header['Content-Type'] = 'application/json'
    final_header['sk-game-role'] = f"3_{role_id}_{server_id}"

    response = requests.post(ENDFIELD_SIGN_URL, headers=final_header, timeout=15)
    resp = response.json()

    if resp['code'] == 0:
        data = resp['data']
        awards = []
        resource_map = data.get('resourceInfoMap', {})
        for award_id in data.get('awardIds', []):
            info = resource_map.get(award_id.get('id', ''), {})
            name = info.get('name', '未知物品')
            count = info.get('count', 0)
            awards.append(f"{name}x{count}")
        return {'success': True, 'awards': awards}
    else:
        msg = resp.get('message', '未知错误')
        if '已签到' in msg or '重复' in msg or 'repeat' in msg.lower():
            return {'success': True, 'awards': [], 'repeated': True}
        return {'success': False, 'error': msg}


def main():
    print(f"[终末地签到] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not TOKEN:
        print("错误: 未设置 SKLAND_TOKEN")
        print_notify_results(send_notification("终末地签到失败", "未设置 SKLAND_TOKEN"))
        sys.exit(1)

    try:
        init_did()
    except Exception as e:
        import traceback
        print(f"dId 初始化失败: {str(e)}")
        print(f"\n详细错误信息：\n{traceback.format_exc()}")
        print_notify_results(send_notification("终末地签到失败", f"dId 初始化失败: {str(e)}"))
        sys.exit(1)

    token_list = TOKEN.split(',')
    results = []
    all_success = True

    for idx, raw_token in enumerate(token_list):
        raw_token = raw_token.strip()
        if not raw_token:
            continue

        try:
            cred_resp = login(raw_token)
            sign_token = cred_resp['token']
            cred = cred_resp['cred']

            characters = get_endfield_characters(cred_resp)

            if not characters:
                results.append("未找到终末地角色")
                all_success = False
                continue

            for char in characters:
                name = char['nickName']
                role_id = char['roleId']
                server_id = char['serverId']
                role_label = f"{name} Lv{char.get('level', 0)}"
                account_label = f"账号{idx + 1}"

                result = do_endfield_sign(sign_token, cred, role_id, server_id)

                if result.get('repeated'):
                    result_text = "今天已签到（重复签到）"
                    ok = True
                elif result['success']:
                    award_str = ', '.join(result['awards']) if result['awards'] else '无奖励'
                    result_text = f"签到成功，获得: {award_str}"
                    ok = True
                else:
                    result_text = f"签到失败 - {result['error']}"
                    ok = False

                entry = format_sign_entry("终末地", account_label, role_label, result_text)
                results.append(entry)
                print(entry)

        except Exception as e:
            results.append(f"账号_{idx + 1}: 处理失败 - {str(e)}")
            all_success = False

    report = "\n".join(results)
    title = "终末地签到成功" if all_success else "终末地签到部分失败"
    print(f"\n{report}")
    print_notify_results(send_notification(title, report))

    if not all_success:
        sys.exit(1)


if __name__ == "__main__":
    main()
