#!/usr/bin/env python3
"""
明日方舟：终末地 签到脚本 - GitHub Actions 专用版
参考 nonebot-plugin-skland 项目的终末地签到逻辑
"""

import hashlib
import hmac
import json
import os
import sys
import time
import base64
import gzip
import uuid
import requests
from datetime import datetime
from urllib import parse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.base import Cipher
from cryptography.hazmat.primitives.ciphers.modes import ECB, CBC

# ================== 配置 ==================
TOKEN = os.environ.get('SKLAND_TOKEN', '')

# ================== 数美配置 ==================
SM_CONFIG = {
    "organization": "UWXspnCCJN4sfYlNfqps",
    "appId": "default",
    "publicKey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmxMNr7n8ZeT0tE1R9j/mPixoinPkeM+k4VGIn/s0k7N5rJAfnZ0eMER+QhwFvshzo0LNmeUkpR8uIlU/GEVr8mN28sKmwd2gpygqj0ePnBmOW4v0ZVwbSYK+izkhVFk2V/doLoMbWy6b+UnA8mkjvg0iYWRByfRsK2gdl7llqCwIDAQAB",
    "protocol": "https",
    "apiHost": "fp-it.portal101.cn"
}

PK = serialization.load_der_public_key(base64.b64decode(SM_CONFIG['publicKey']))

app_code = '4ca99fa6b56cc2ba'

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

binding_url = "https://zonai.skland.com/api/v1/game/player/binding"
grant_code_url = "https://as.hypergryph.com/user/oauth2/v2/grant"
cred_code_url = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"
endfield_sign_url = "https://zonai.skland.com/web/v1/game/endfield/attendance"
devices_info_url = "https://fp-it.portal101.cn/deviceprofile/v4"

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
    iv = '0102030405060708'
    cipher = Cipher(AES(k), CBC(iv.encode('utf-8')))
    v += b'\x00'
    while len(v) % 16 != 0:
        v += b'\x00'
    return cipher.encryptor().update(v).hex()


def GZIP(o: dict):
    json_str = json.dumps(o, ensure_ascii=False)
    compressed = gzip.compress(json_str.encode('utf-8'), 2, mtime=0)
    return base64.b64encode(compressed)


def get_tn(o: dict):
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
    t = time.localtime()
    _time = f'{t.tm_year}{t.tm_mon:02d}{t.tm_mday:02d}{t.tm_hour:02d}{t.tm_min:02d}{t.tm_sec:02d}'
    uid = str(uuid.uuid4())
    md5_uid = hashlib.md5(uid.encode('utf-8')).hexdigest()
    smsk_web = hashlib.md5(f'smsk_web_{_time}{md5_uid}00'.encode('utf-8')).hexdigest()[:14]
    return f'{_time}{md5_uid}00{smsk_web}0'


def get_d_id():
    uid = str(uuid.uuid4()).encode('utf-8')
    priId = hashlib.md5(uid).hexdigest()[:16]
    ep = PK.encrypt(uid, padding.PKCS1v15())
    ep = base64.b64encode(ep).decode('utf-8')

    browser = BROWSER_ENV.copy()
    current_time = int(time.time() * 1000)
    browser.update({
        'vpw': str(uuid.uuid4()),
        'svm': current_time,
        'trees': str(uuid.uuid4()),
        'pmf': current_time
    })

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
    des_result = _AES(GZIP(_DES(des_target)), priId.encode('utf-8'))

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


# ================== 签名与登录 ==================
def parse_token(token_str):
    try:
        data = json.loads(token_str)
        if 'data' in data and 'content' in data['data']:
            return data['data']['content']
    except:
        pass
    return token_str


def generate_signature(token: str, path, body_or_query):
    t = str(int(time.time()) - 2)
    token = token.encode('utf-8')
    header_ca = json.loads(json.dumps(header_for_sign))
    header_ca['timestamp'] = t
    header_ca_str = json.dumps(header_ca, separators=(',', ':'))
    s = path + body_or_query + t + header_ca_str
    hex_s = hmac.new(token, s.encode('utf-8'), hashlib.sha256).hexdigest()
    md5 = hashlib.md5(hex_s.encode('utf-8')).hexdigest()
    return md5, header_ca


def get_sign_header(url: str, method, body, h, token):
    p = parse.urlparse(url)
    if method.lower() == 'get':
        h['sign'], header_ca = generate_signature(token, p.path, p.query)
    else:
        h['sign'], header_ca = generate_signature(token, p.path, json.dumps(body) if body else '')
    for i in header_ca:
        h[i] = header_ca[i]
    return h


def get_grant_code(token):
    response = requests.post(grant_code_url, json={
        'appCode': app_code,
        'token': token,
        'type': 0
    }, headers=header_login, timeout=10)
    resp = response.json()
    if response.status_code != 200 or resp.get('status') != 0:
        raise Exception(f'获取认证代码失败：{resp.get("msg", "未知错误")}')
    return resp['data']['code']


def get_cred(grant):
    resp = requests.post(cred_code_url, json={
        'code': grant,
        'kind': 1
    }, headers=header_login, timeout=10).json()
    if resp['code'] != 0:
        raise Exception(f'获取cred失败：{resp["message"]}')
    return resp['data']


# ================== 终末地核心功能 ==================
def get_endfield_characters(cred_resp):
    """获取绑定的终末地角色列表"""
    sign_token = cred_resp['token']
    cred = cred_resp['cred']

    current_header = header.copy()
    current_header['cred'] = cred

    final_header = get_sign_header(binding_url, 'get', None, current_header, sign_token)
    response = requests.get(binding_url, headers=final_header, timeout=15)
    resp = response.json()

    if resp['code'] != 0:
        raise Exception(f"获取角色列表失败：{resp['message']}")

    characters = []
    for entry in resp['data']['list']:
        if entry.get('appCode') == 'endfield':
            for char in entry.get('bindingList', []):
                characters.append({
                    'uid': char.get('uid', ''),
                    'nickName': char.get('nickName', '未知角色'),
                    'channelMasterId': char.get('channelMasterId', ''),
                })
    return characters


def do_endfield_sign(sign_token, cred, role_id, server_id):
    """执行终末地签到"""
    current_header = header.copy()
    current_header['cred'] = cred

    final_header = get_sign_header(endfield_sign_url, 'post', None, current_header, sign_token)
    final_header['Content-Type'] = 'application/json'
    final_header['sk-game-role'] = f"3_{role_id}_{server_id}"

    response = requests.post(endfield_sign_url, headers=final_header, timeout=15)
    resp = response.json()

    if resp['code'] == 0:
        data = resp['data']
        awards = []
        resource_map = data.get('resourceInfoMap', {})
        for award_id in data.get('awardIds', []):
            info = resource_map.get(award_id.get('id', ''), {})
            name = info.get('name', '未知物品')
            count = info.get('count', 0)
            awards.append(f"{name}×{count}")
        return {'success': True, 'awards': awards}
    else:
        msg = resp.get('message', '未知错误')
        if '已签到' in msg or 'repeat' in msg.lower():
            return {'success': True, 'awards': [], 'repeated': True}
        return {'success': False, 'error': msg}


def main():
    print("=" * 50)
    print("明日方舟：终末地 签到脚本")
    print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    if not TOKEN:
        print("错误：请在 GitHub Secrets 中设置 SKLAND_TOKEN")
        sys.exit(1)

    # 初始化 dId
    try:
        d_id = get_d_id()
        header_login['dId'] = d_id
        header_for_sign['dId'] = d_id
        print("设备ID生成成功")
    except Exception as e:
        print(f"dId 初始化失败：{str(e)}")
        sys.exit(1)

    token_list = TOKEN.split(',')
    all_success = True

    for idx, raw_token in enumerate(token_list):
        raw_token = raw_token.strip()
        if not raw_token:
            continue

        token_id = f"账号_{idx + 1}"
        print(f"\n--- 处理 {token_id} ---")

        try:
            token = parse_token(raw_token)
            grant_code = get_grant_code(token)
            cred_resp = get_cred(grant_code)
            characters = get_endfield_characters(cred_resp)

            if not characters:
                print("  未找到终末地角色，请确认已在森空岛绑定终末地账号")
                all_success = False
                continue

            print(f"  找到 {len(characters)} 个终末地角色")

            sign_token = cred_resp['token']
            cred = cred_resp['cred']

            for char in characters:
                name = char['nickName']
                uid = char['uid']
                server_id = char['channelMasterId']

                print(f"  签到角色: {name} (uid={uid})")
                result = do_endfield_sign(sign_token, cred, uid, server_id)

                if result.get('repeated'):
                    print(f"    今天已经签到过了")
                elif result['success']:
                    award_str = ', '.join(result['awards']) if result['awards'] else '无奖励'
                    print(f"    签到成功，获得: {award_str}")
                else:
                    print(f"    签到失败: {result['error']}")
                    all_success = False

        except Exception as e:
            print(f"  {token_id} 处理失败: {str(e)}")
            all_success = False

    if all_success:
        print("\n签到任务完成")
    else:
        print("\n部分账号签到失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
