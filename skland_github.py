#!/usr/bin/env python3
"""
森空岛签到脚本 - GitHub Actions 专用版
修复Webhook通知问题
"""

import hashlib
import hmac
import json
import os
import time
import uuid
import base64
import requests
from datetime import datetime
from urllib import parse

# ================== 配置 ==================
TOKEN = os.environ.get('SKLAND_TOKEN', '')
WECHAT_WEBHOOK_URL = os.environ.get('WECHAT_WEBHOOK_URL', '')

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
    'dId': 'test_device_id_123456'
}

header_for_sign = {
    'platform': '',
    'timestamp': '',
    'dId': 'test_device_id_123456',
    'vName': ''
}

# 接口URL
sign_url = "https://zonai.skland.com/api/v1/game/attendance"
binding_url = "https://zonai.skland.com/api/v1/game/player/binding"
grant_code_url = "https://as.hypergryph.com/user/oauth2/v2/grant"
cred_code_url = "https://zonai.skland.com/web/v1/user/auth/generate_cred_by_code"

def simple_did():
    """生成简化的设备ID"""
    return 'B' + hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()

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

def send_wechat_notification(subject, message, max_retries=3):
    """发送企业微信通知（可选）"""
    if not WECHAT_WEBHOOK_URL:
        print("⚠️  未设置企业微信Webhook URL，跳过通知")
        return
    
    print(f"📤 尝试发送企业微信通知...")
    print(f"   Webhook URL: {'已设置' if WECHAT_WEBHOOK_URL else '未设置'}")
    print(f"   主题: {subject}")
    
    # 企业微信Webhook格式
    payload = {
        "msgtype": "text",
        "text": {
            "content": f"【森空岛签到】{subject}\n{message}"
        }
    }
    
    for attempt in range(max_retries):
        try:
            print(f"  第{attempt+1}次尝试发送...")
            response = requests.post(
                WECHAT_WEBHOOK_URL, 
                json=payload, 
                timeout=15,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"  响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  响应内容: {result}")
                
                if result.get("errcode") == 0:
                    print("✅ 企业微信通知发送成功")
                    return True
                else:
                    print(f"❌ 企业微信通知发送失败: {result.get('errmsg', '未知错误')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"❌ 响应解析失败: {str(e)}")
        except Exception as e:
            print(f"❌ 未知错误: {str(e)}")
        
        if attempt < max_retries - 1:
            wait_time = 5 * (attempt + 1)  # 指数退避
            print(f"  等待{wait_time}秒后重试...")
            time.sleep(wait_time)
    
    print("❌ 企业微信通知发送失败，已达到最大重试次数")
    return False

def main():
    """主函数"""
    print("=" * 50)
    print("森空岛签到脚本 - 简化版")
    print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 检查是否有token
    if not TOKEN:
        error_msg = "❌ 错误：请在 GitHub Secrets 中设置 SKLAND_TOKEN"
        print(error_msg)
        send_wechat_notification("签到失败", error_msg)
        return
    
    # 生成设备ID
    d_id = simple_did()
    header_login['dId'] = d_id
    header_for_sign['dId'] = d_id
    print(f"✅ 使用简化设备ID")
    
    # 解析token
    tokens = {}
    token_list = TOKEN.split(',')
    for i, token in enumerate(token_list):
        token = token.strip()
        if token:
            # 尝试解析为JSON格式
            try:
                data = json.loads(token)
                if 'data' in data and 'content' in data['data']:
                    token = data['data']['content']
            except:
                pass  # 如果不是JSON，直接使用原token
            
            token_id = f"token_{i+1}"
            tokens[token_id] = token
    
    if not tokens:
        error_msg = "❌ 未找到有效token"
        print(error_msg)
        send_wechat_notification("签到失败", error_msg)
        return
    
    print(f"✅ 找到 {len(tokens)} 个账号，开始签到...")
    
    # 执行签到
    all_results = []
    success_count = 0
    repeated_count = 0
    failed_count = 0
    total_characters = 0
    
    for account_id, token in tokens.items():
        result = do_sign_for_account(account_id, token)
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
    elif repeated_count > 0:
        subject = f"重复签到 ({repeated_count}个重复)"
    elif failed_count > 0:
        subject = f"签到失败 ({failed_count}个失败)"
    else:
        subject = "签到完成"
    
    report = f"""📊 签到统计：
• 账号总数: {len(all_results)}
• 签到成功: {success_count}
• 重复签到: {repeated_count}
• 签到失败: {failed_count}
• 角色总数: {total_characters}

📋 详细结果："""

    # 限制详细结果长度，避免消息过长
    max_results_to_show = 3  # 每个账号最多显示3个结果
    for result in all_results:
        status_icon = "✅" if result['status'] == 'success' else "🔄" if result['status'] == 'repeated' else "❌"
        report += f"\n\n{status_icon} 账号: {result['account']}"
        
        # 只显示部分结果，避免消息过长
        results_to_show = result['results'][:max_results_to_show]
        for res in results_to_show:
            report += f"\n  {res}"
        
        if len(result['results']) > max_results_to_show:
            report += f"\n  ...（还有{len(result['results']) - max_results_to_show}个结果未显示）"
    
    # 添加失败摘要
    if failed_count > 0:
        failed_accounts = [r for r in all_results if r['status'] == 'failed']
        report += f"\n\n❌ 失败账号摘要："
        for fail in failed_accounts[:5]:  # 最多显示5个失败账号
            report += f"\n  {fail['account']}: {fail['results'][0] if fail['results'] else '未知错误'}"
    
    print(report)
    
    # 发送通知
    print("\n📨 发送通知...")
    notification_sent = send_wechat_notification(subject, report)
    
    if notification_sent:
        print("✅ 通知发送流程完成")
    elif not WECHAT_WEBHOOK_URL:
        print("ℹ️  未配置Webhook URL，跳过通知")
    else:
        print("⚠️  通知发送失败，但签到过程已完成")
    
    # 如果全部失败，退出码设为1（让GitHub Actions标记为失败）
    if failed_count == len(all_results):
        print("\n❌ 所有账号签到失败")
        exit(1)
    else:
        print("\n✅ 签到任务完成")

if __name__ == "__main__":
    main()