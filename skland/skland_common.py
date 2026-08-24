#!/usr/bin/env python3
"""森空岛 API 公共模块 - 数美设备ID、签名、登录"""

import hashlib
import hmac
import json
import os
import time
import uuid
import base64
import gzip
import requests
from urllib import parse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.base import Cipher
from cryptography.hazmat.primitives.ciphers.modes import ECB, CBC

# ================== 数美配置 ==================
SM_CONFIG = {
    "organization": "UWXspnCCJN4sfYlNfqps",
    "appId": "default",
    "publicKey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmxMNr7n8ZeT0tE1R9j/mPixoinPkeM+k4VGIn/s0k7N5rJAfnZ0eMER+QhwFvshzo0LNmeUkpR8uIlU/GEVr8mN28sKmwd2gpygqj0ePnBmOW4v0ZVwbSYK+izkhVFk2V/doLoMbWy6b+UnA8mkjvg0iYWRByfRsK2gdl7llqCwIDAQAB",
    "protocol": "https",
    "apiHost": "fp-it.portal101.cn"
}

PK = serialization.load_der_public_key(base64.b64decode(SM_CONFIG['publicKey']))

APP_CODE = '4ca99fa6b56cc2ba'

# ================== 请求头 ==================
HEADER = {
    'cred': '',
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close'
}

HEADER_LOGIN = {
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close',
    'dId': ''
}

HEADER_FOR_SIGN = {
    'platform': '',
    'timestamp': '',
    'dId': '',
    'vName': ''
}

# ================== URL ==================
BINDING_URL = "https://zonai.skland.com/api/v1/game/player/binding"
GRANT_CODE_URL = "https://as.hypergryph.com/user/oauth2/v2/grant"
CRED_CODE_URL = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"
REFRESH_TOKEN_URL = "https://zonai.skland.com/api/v1/auth/refresh"
ARK_SIGN_URL = "https://zonai.skland.com/api/v1/game/attendance"
ENDFIELD_SIGN_URL = "https://zonai.skland.com/web/v1/game/endfield/attendance"
DEVICES_INFO_URL = "https://fp-it.portal101.cn/deviceprofile/v4"

# ================== 数美浏览器环境 ==================
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


def _GZIP(o: dict):
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
    des_result = _AES(_GZIP(_DES(des_target)), priId.encode('utf-8'))

    try:
        response = requests.post(
            DEVICES_INFO_URL,
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


# ================== 签名 ==================
def generate_signature(token: str, path, body_or_query):
    t = str(int(time.time()) - 2)
    token_bytes = token.encode('utf-8')
    header_ca = json.loads(json.dumps(HEADER_FOR_SIGN))
    header_ca['timestamp'] = t
    header_ca_str = json.dumps(header_ca, separators=(',', ':'))
    s = path + body_or_query + t + header_ca_str
    hex_s = hmac.new(token_bytes, s.encode('utf-8'), hashlib.sha256).hexdigest()
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


# ================== 登录 ==================
def parse_token(token_str):
    try:
        data = json.loads(token_str)
        if 'data' in data and 'content' in data['data']:
            return data['data']['content']
    except:
        pass
    return token_str


def get_grant_code(token):
    response = requests.post(GRANT_CODE_URL, json={
        'appCode': APP_CODE,
        'token': token,
        'type': 0
    }, headers=HEADER_LOGIN, timeout=10)
    resp = response.json()
    if response.status_code != 200 or resp.get('status') != 0:
        raise Exception(f'获取认证代码失败：{resp.get("msg", "未知错误")}')
    return resp['data']['code']


def get_cred(grant):
    resp = requests.post(CRED_CODE_URL, json={
        'code': grant,
        'kind': 1
    }, headers=HEADER_LOGIN, timeout=10).json()
    if resp['code'] != 0:
        raise Exception(f'获取cred失败：{resp["message"]}')
    return resp['data']


def refresh_token(cred):
    response = requests.get(REFRESH_TOKEN_URL, headers={**HEADER, 'cred': cred}, timeout=10)
    resp = response.json()
    if resp.get('code') != 0:
        raise Exception(f"刷新token失败：{resp.get('message')}")
    return resp['data']['token']


def init_did():
    """初始化设备ID：优先复用本地缓存的已注册设备，失败才重新生成"""
    did_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".did")

    if os.path.exists(did_file):
        try:
            with open(did_file, encoding="utf-8") as f:
                cached = f.read().strip()
            if cached:
                HEADER_LOGIN['dId'] = cached
                HEADER_FOR_SIGN['dId'] = cached
                print(f"\u2705 复用已注册设备ID: {cached[:10]}...")
                return cached
        except Exception:
            pass

    d_id = get_d_id()
    HEADER_LOGIN['dId'] = d_id
    HEADER_FOR_SIGN['dId'] = d_id
    try:
        with open(did_file, "w", encoding="utf-8") as f:
            f.write(d_id)
    except Exception:
        pass
    return d_id


def login(token_str):
    """完整的登录流程：token -> grant_code -> cred -> refresh_token"""
    token = parse_token(token_str)
    grant_code = get_grant_code(token)
    cred_resp = get_cred(grant_code)
    try:
        cred_resp['token'] = refresh_token(cred_resp['cred'])
    except Exception:
        pass
    return cred_resp
