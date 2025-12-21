#!/usr/bin/env python3
"""
森空岛自动签到脚本 - GitHub Actions版本
支持多账号、动态设备ID、企业微信通知
"""
import os
import json
import time
import random
import hashlib
import hmac
import base64
import gzip
import uuid
from datetime import datetime
from urllib import parse

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
from cryptography.hazmat.primitives.ciphers.base import Cipher
from cryptography.hazmat.primitives.ciphers.modes import CBC, ECB

# ================== 配置 ==================
app_code = '4ca99fa6b56cc2ba'

# ================== 简化的数美设备ID生成 ==================
def generate_shumei_device_id():
    """生成数美设备ID"""
    try:
        # 数美配置
        SM_CONFIG = {
            "organization": "UWXspnCCJN4sfYlNfqps",
            "appId": "default",
            "publicKey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmxMNr7n8ZeT0tE1R9j/mPixoinPkeM+k4VGIn/s0k7N5rJAfnZ0eMER+QhwFvshzo0LNmeUkpR8uIlU/GEVr8mN28sKmwd2gpygqj0ePnBmOW4v0ZVwbSYK+izkhVFk2V/doLoMbWy6b+UnA8mkjvg0iYWRByfRsK2gdl7llqCwIDAQAB"
        }
        
        # 加载RSA公钥
        PK = serialization.load_der_public_key(base64.b64decode(SM_CONFIG['publicKey']))
        
        # 生成UUID
        uid = str(uuid.uuid4())
        priId = hashlib.md5(uid.encode()).hexdigest()[0:16]
        
        # RSA加密
        ep = PK.encrypt(uid.encode(), padding.PKCS1v15())
        ep = base64.b64encode(ep).decode()
        
        # 浏览器环境
        browser_env = {
            'plugins': 'MicrosoftEdgePDFPluginPortableDocumentFormatinternal-pdf-viewer1,MicrosoftEdgePDFViewermhjfbmdgcfjbbpaeojofohoefgiehjai1',
            'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
            'canvas': '259ffe69',
            'timezone': -480,
            'platform': 'Win32',
            'url': 'https://www.skland.com/',
            'referer': '',
            'res': '1920_1080_24_1.25',
            'clientSize': '0_0_1080_1920_1920_1080_1920_1080',
            'status': '0011',
        }
        
        current_time = int(time.time() * 1000)
        browser_env.update({
            'vpw': str(uuid.uuid4()),
            'svm': current_time,
            'trees': str(uuid.uuid4()),
            'pmf': current_time
        })
        
        # 构建请求数据
        des_target = {
            **browser_env,
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
        
        # 计算tn
        des_target['tn'] = hashlib.md5(get_tn(des_target).encode()).hexdigest()
        
        # DES加密
        des_result = _AES(GZIP(_DES(des_target)), priId.encode())
        
        # 请求数美API
        devices_info_url = "https://fp-it.portal101.cn/deviceprofile/v4"
        response = requests.post(devices_info_url, json={
            'appId': 'default',
            'compress': 2,
            'data': des_result,
            'encode': 5,
            'ep': ep,
            'organization': SM_CONFIG['organization'],
            'os': 'web'
        }, timeout=10)
        
        if response.status_code == 200:
            resp = response.json()
            if resp.get('code') == 1100:
                device_id = 'B' + resp['detail']['deviceId']
                print(f"✅ 成功生成数美设备ID: {device_id}")
                return device_id
        
        print("❌ 数美API请求失败，使用备用方案")
        return generate_random_device_id()
            
    except Exception as e:
        print(f"❌ 数美设备ID生成失败: {str(e)}")
        return generate_random_device_id()

def get_smid():
    """生成SMID"""
    t = time.localtime()
    _time = '{}{:0>2d}{:0>2d}{:0>2d}{:0>2d}{:0>2d}'.format(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    uid = str(uuid.uuid4())
    v = _time + hashlib.md5(uid.encode()).hexdigest() + '00'
    smsk_web = hashlib.md5(('smsk_web_' + v).encode()).hexdigest()[0:14]
    return v + smsk_web + '0'

def get_tn(o: dict):
    """计算tn值"""
    sorted_keys = sorted(o.keys())
    result_list = []
    
    for i in sorted_keys:
        v = o[i]
        if isinstance(v, (int, float)):
            v = str(v * 10000)
        elif isinstance(v, dict):
            v = get_tn(v)
        result_list.append(v)
    return ''.join(result_list)

def _DES(o: dict):
    """DES加密"""
    DES_RULE = {
        "appId": {"cipher": "DES", "is_encrypt": 1, "key": "uy7mzc4h", "obfuscated_name": "xx"},
        "canvas": {"cipher": "DES", "is_encrypt": 1, "key": "snrn887t", "obfuscated_name": "yk"},
        "clientSize": {"cipher": "DES", "is_encrypt": 1, "key": "cpmjjgsu", "obfuscated_name": "zx"},
        "organization": {"cipher": "DES", "is_encrypt": 1, "key": "78moqjfc", "obfuscated_name": "dp"},
        "os": {"cipher": "DES", "is_encrypt": 1, "key": "je6vk6t4", "obfuscated_name": "pj"},
        "platform": {"cipher": "DES", "is_encrypt": 1, "key": "pakxhcd2", "obfuscated_name": "gm"},
        "plugins": {"cipher": "DES", "is_encrypt": 1, "key": "v51m3pzl", "obfuscated_name": "kq"},
        "pmf": {"cipher": "DES", "is_encrypt": 1, "key": "2mdeslu3", "obfuscated_name": "vw"},
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
        "vpw": {"cipher": "DES", "is_encrypt": 1, "key": "r9924ab5", "obfuscated_name": "ca"}
    }
    
    result = {}
    for i in o.keys():
        if i in DES_RULE:
            rule = DES_RULE[i]
            res = o[i]
            if rule['is_encrypt'] == 1:
                try:
                    c = Cipher(TripleDES(rule['key'].encode()), ECB())
                    data = str(res).encode()
                    data += b'\x00' * 8
                    res = base64.b64encode(c.encryptor().update(data)).decode()
                except:
                    pass
            result[rule['obfuscated_name']] = res
        else:
            result[i] = o[i]
    return result

def _AES(v: bytes, k: bytes):
    """AES加密"""
    try:
        iv = '0102030405060708'.encode()
        key = AES(k)
        c = Cipher(key, CBC(iv))
        encryptor = c.encryptor()
        
        v += b'\x00'
        while len(v) % 16 != 0:
            v += b'\x00'
        
        encrypted = encryptor.update(v) + encryptor.finalize()
        return encrypted.hex()
    except Exception as e:
        print(f"AES加密失败: {str(e)}")
        return hashlib.md5(v + k).hexdigest()

def GZIP(o: dict):
    """GZIP压缩"""
    json_str = json.dumps(o, ensure_ascii=False)
    stream = gzip.compress(json_str.encode(), 2, mtime=0)
    return stream

def generate_random_device_id():
    """生成随机设备ID"""
    random_part = ''.join(random.choices('0123456789abcdef', k=31))
    return f"B{random_part}"

def get_device_id():
    """获取设备ID"""
    device_mode = os.environ.get('DEVICE_MODE', 'smart')
    fixed_id = os.environ.get('FIXED_DEVICE_ID')
    
    if fixed_id:
        print(f"📱 使用固定设备ID: {fixed_id}")
        return fixed_id
    
    if device_mode == 'random':
        device_id = generate_random_device_id()
        print(f"🎲 生成随机设备ID: {device_id}")
        return device_id
    
    if device_mode == 'shumei':
        return generate_shumei_device_id()
    
    # smart模式：70%使用随机，30%使用数美
    if random.random() < 0.7:
        device_id = generate_random_device_id()
        print(f"🎲 生成随机设备ID: {device_id}")
        return device_id
    else:
        return generate_shumei_device_id()

# ================== HTTP 请求头 ==================
def get_headers():
    """获取请求头"""
    device_id = get_device_id()
    
    return {
        'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close',
        'dId': device_id
    }

def get_auth_headers(cred):
    """获取认证请求头"""
    return {
        'cred': cred,
        'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close'
    }

# ================== 核心签到函数 ==================
def generate_signature(token: str, path, body_or_query, device_id):
    """生成签名"""
    t = str(int(time.time()) - 2)
    header_ca = {
        'platform': '',
        'timestamp': t,
        'dId': device_id,
        'vName': ''
    }
    header_ca_str = json.dumps(header_ca, separators=(',', ':'))
    s = path + body_or_query + t + header_ca_str
    hex_s = hmac.new(token.encode(), s.encode(), hashlib.sha256).hexdigest()
    md5 = hashlib.md5(hex_s.encode()).hexdigest()
    return md5, header_ca

def get_sign_header(url: str, method, body, headers, token, device_id):
    """构建带签名的请求头"""
    p = parse.urlparse(url)
    if method.lower() == 'get':
        sign, header_ca = generate_signature(token, p.path, p.query, device_id)
    else:
        body_str = json.dumps(body, ensure_ascii=False) if body else ''
        sign, header_ca = generate_signature(token, p.path, body_str, device_id)
    
    headers['sign'] = sign
    for key, value in header_ca.items():
        headers[key] = value
    
    return headers

def parse_user_token(t):
    """解析用户token"""
    try:
        t = json.loads(t)
        return t['data']['content']
    except:
        return t

def get_cred_by_token(token):
    """通过token获取cred"""
    try:
        # 获取grant code
        print("🔄 正在获取grant code...")
        headers = get_headers()
        response = requests.post(
            "https://as.hypergryph.com/user/oauth2/v2/grant",
            headers=headers,
            json={'appCode': app_code, 'token': token, 'type': 0},
            timeout=10
        )
        resp = response.json()
        
        if resp.get('status') != 0:
            raise Exception(f'获取认证代码失败：{resp.get("msg", "未知错误")}')
        
        grant = resp['data']['code']
        print(f"✅ 获取到grant code: {grant[:10]}...")
        
        # 获取cred
        print("🔄 正在获取cred...")
        response2 = requests.post(
            "https://zonai.skland.com/web/v1/user/auth/generate_cred_by_code",
            headers=headers,
            json={'code': grant, 'kind': 1},
            timeout=10
        )
        resp2 = response2.json()
        
        if resp2.get('code') != 0:
            error_msg = resp2.get("message", "未知错误")
            print(f"❌ 获取cred失败: {error_msg}")
            
            # 尝试备选方案
            print("🔄 尝试备选方案...")
            response3 = requests.post(
                "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code",
                headers=headers,
                json={'code': grant, 'kind': 1},
                timeout=10
            )
            resp3 = response3.json()
            
            if resp3.get('code') == 0:
                print(f"✅ 备选方案成功获取cred: {resp3['data']['cred'][:10]}...")
                return resp3['data']
            else:
                raise Exception(f'获取cred失败：{error_msg}')
        
        print(f"✅ 获取到cred: {resp2['data']['cred'][:10]}...")
        return resp2['data']
        
    except Exception as e:
        raise Exception(f"获取凭证失败：{str(e)}")

def get_binding_list(token, cred, device_id):
    """获取绑定的角色列表"""
    try:
        # 构建请求头
        headers = get_auth_headers(cred)
        url = "https://zonai.skland.com/api/v1/game/player/binding"
        headers = get_sign_header(url, 'get', None, headers, token, device_id)
        
        print("🔄 正在获取角色列表...")
        response = requests.get(url, headers=headers, timeout=10)
        resp = response.json()
        
        if resp.get('code') != 0:
            error_msg = resp.get('message', '未知错误')
            print(f"⚠️ 角色列表请求失败：{error_msg}")
            return []
        
        v = []
        for i in resp['data']['list']:
            if i.get('appCode') == 'arknights':
                v.extend(i.get('bindingList', []))
        
        if not v:
            print("⚠️ 在角色列表中未找到明日方舟账号")
        else:
            print(f"✅ 找到 {len(v)} 个明日方舟角色")
        return v
        
    except Exception as e:
        print(f"⚠️ 获取角色列表异常：{str(e)}")
        return []

def do_sign(user_token):
    """执行签到"""
    try:
        # 获取凭证
        print("🔄 正在获取凭证...")
        cred_resp = get_cred_by_token(user_token)
        token = cred_resp['token']
        cred = cred_resp['cred']
        device_id = get_headers()['dId']
        print(f"✅ 凭证获取成功: token={token[:10]}..., cred={cred[:10]}...")
        
    except Exception as e:
        error_msg = f'获取凭证失败：{str(e)}'
        print(f"❌ {error_msg}")
        return {
            'account': user_token[:10] if len(user_token) > 10 else user_token,
            'results': [error_msg],
            'status': 'failed'
        }
    
    # 获取角色列表
    characters = get_binding_list(token, cred, device_id)
    
    if not characters:
        result_msg = "未找到可签到的角色"
        print(f"⚠️ {result_msg}")
        return {
            'account': token[:10] if len(token) > 10 else token,
            'results': [result_msg],
            'status': 'failed'
        }
    
    # 执行签到
    results = []
    status_list = []
    
    for character in characters:
        character_name = character.get("nickName", "未知角色")
        character_uid = character.get('uid', '未知UID')
        try:
            body = {'gameId': 1, 'uid': character_uid}
            
            # 构建请求头
            headers = get_auth_headers(cred)
            url = "https://zonai.skland.com/api/v1/game/attendance"
            headers = get_sign_header(url, 'post', body, headers, token, device_id)
            
            # 发送签到请求
            print(f"🔄 正在为 {character_name}({character_uid}) 签到...")
            response = requests.post(url, headers=headers, json=body, timeout=10)
            resp = response.json()
            
            if resp.get('code') == 0:
                awards = resp['data']['awards']
                award_info = []
                for j in awards:
                    res = j['resource']
                    count = j.get('count', 1)
                    award_info.append(f"{res['name']}×{count}")
                result_msg = f"角色 {character_name} 签到成功，获得: {', '.join(award_info)}"
                results.append(result_msg)
                status_list.append('success')
                print(f"✅ {result_msg}")
            elif resp.get('code') == 10001 and '请勿重复签到' in resp.get('message', ''):
                result_msg = f"角色 {character_name} 今天已经签到过了！"
                results.append(result_msg)
                status_list.append('repeated')
                print(f"🔄 {result_msg}")
            elif '请勿重复签到' in resp.get('message', ''):
                result_msg = f"角色 {character_name} 今天已经签到过了！"
                results.append(result_msg)
                status_list.append('repeated')
                print(f"🔄 {result_msg}")
            else:
                result_msg = f"角色 {character_name} 签到失败：{resp.get('message', '未知错误')}"
                results.append(result_msg)
                status_list.append('failed')
                print(f"❌ {result_msg}")
                
        except Exception as e:
            result_msg = f'角色 {character_name} 签到异常：{str(e)}'
            results.append(result_msg)
            status_list.append('failed')
            print(f"❌ {result_msg}")
    
    overall_status = 'success' if 'success' in status_list else \
                   ('repeated' if 'repeated' in status_list and 'failed' not in status_list else 'failed')
    
    return {
        'account': token[:10] if len(token) > 10 else token,
        'results': results,
        'status': overall_status,
        'character_status': status_list
    }

# ================== 通知功能 ==================
def send_wechatwork_notification(subject, message):
    """通过企业微信Webhook发送通知"""
    webhook_url = os.environ.get('WECHAT_WEBHOOK_URL')
    
    if not webhook_url:
        print("⚠️ 未配置企业微信Webhook URL，跳过通知")
        return
    
    msg_content = f"【{subject}】\n{message}"
    payload = {
        "msgtype": "text",
        "text": {
            "content": msg_content
        }
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200 and response.json().get("errcode") == 0:
            print("✅ 企业微信通知发送成功")
        else:
            print(f"❌ 企业微信通知发送失败: {response.text}")
    except Exception as e:
        print(f"⚠️ 企业微信通知请求失败: {str(e)}")

def send_github_summary(results):
    """发送GitHub Actions摘要"""
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write("## 森空岛签到结果\n\n")
            f.write(f"**执行时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            total = len(results)
            success = sum(1 for r in results if r['status'] == 'success')
            repeated = sum(1 for r in results if r['status'] == 'repeated')
            failed = sum(1 for r in results if r['status'] == 'failed')
            
            f.write(f"📊 **账号总数:** {total}\n")
            f.write(f"✅ **签到成功:** {success}\n")
            f.write(f"🔄 **重复签到:** {repeated}\n")
            f.write(f"❌ **签到失败:** {failed}\n\n")
            
            for result in results:
                status_emoji = "✅" if result['status'] == 'success' else "🔄" if result['status'] == 'repeated' else "❌"
                f.write(f"{status_emoji} **账号:** {result['account']}\n")
                for res in result['results']:
                    f.write(f"  - {res}\n")
                f.write("\n")

# ================== 主函数 ==================
def main():
    """签到主流程"""
    print("=" * 50)
    print("🚀 森空岛自动签到任务开始")
    print(f"📅 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏷️  运行环境: GitHub Actions")
    print("=" * 50)
    
    # 从环境变量读取token
    token_env = os.environ.get('TOKEN')
    if not token_env:
        error_msg = "❌ 未设置TOKEN环境变量"
        print(error_msg)
        send_wechatwork_notification("森空岛签到失败", error_msg)
        return {"error": error_msg}
    
    # 处理多个token
    token_list = [parse_user_token(t.strip()) for t in token_env.split(',') if t.strip()]
    print(f"📊 找到 {len(token_list)} 个token，开始执行签到...")
    
    # 收集所有签到结果
    all_results = []
    success_count = 0
    repeated_count = 0
    failed_count = 0
    
    for i, token in enumerate(token_list):
        try:
            print(f"\n{'='*30}")
            print(f"👤 处理第 {i+1}/{len(token_list)} 个账号...")
            print(f"{'='*30}")
            
            sign_result = do_sign(token)
            all_results.append(sign_result)
            
            # 根据状态更新计数器
            if sign_result['status'] == 'success':
                success_count += 1
            elif sign_result['status'] == 'repeated':
                repeated_count += 1
            elif sign_result['status'] == 'failed':
                failed_count += 1
                
        except Exception as e:
            error_msg = f'账号 {i+1} 签到失败：{e}'
            print(f"❌ {error_msg}")
            result = {
                'account': f'账号{i+1}',
                'results': [error_msg],
                'status': 'failed'
            }
            all_results.append(result)
            failed_count += 1
    
    # 发送GitHub Actions摘要
    send_github_summary(all_results)
    
    # 构建通知消息
    notification_msg = f"森空岛签到完成报告\n\n"
    notification_msg += f"📊 账号总数: {len(all_results)}\n"
    notification_msg += f"✅ 签到成功: {success_count}\n"
    notification_msg += f"🔄 重复签到: {repeated_count}\n"
    notification_msg += f"❌ 签到失败: {failed_count}\n"
    notification_msg += f"🕐 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # 添加详细结果
    for result in all_results:
        status_emoji = ""
        if result['status'] == 'success':
            status_emoji = "✅"
        elif result['status'] == 'repeated':
            status_emoji = "🔄"
        elif result['status'] == 'failed':
            status_emoji = "❌"
            
        notification_msg += f"{status_emoji} 账号: {result['account']}\n"
        for res in result['results']:
            notification_msg += f"  {res}\n"
        notification_msg += "\n"
    
    # 发送企业微信通知
    subject = "森空岛签到完成报告"
    if failed_count > 0:
        subject = f"森空岛签到完成 (有{failed_count}个失败)"
    elif success_count > 0:
        subject = f"森空岛签到完成 ({success_count}个成功)"
    elif repeated_count > 0:
        subject = f"森空岛签到完成 ({repeated_count}个重复)"
    
    print("\n📤 发送通知...")
    send_wechatwork_notification(subject, notification_msg)
    
    print("\n" + "=" * 50)
    print("🎉 所有账号签到完成！")
    print("=" * 50)
    
    return {
        "total": len(all_results),
        "success_count": success_count,
        "repeated_count": repeated_count,
        "failed_count": failed_count,
        "results": all_results
    }

if __name__ == "__main__":
    main()