
from __future__ import absolute_import

import hashlib


# 使用MD5加密字符串
def md5_encrypt(text):
    # 创建md5对象
    m = hashlib.md5()
    m.update(text.encode(encoding='utf-8'))
    encrypted = m.hexdigest()
    return encrypted


# 生成安全校验字符串
def gen_sign(params, sign_key):
    keys = []
    for k, v in params.items():
        keys.append(k)
    keys.sort()
    text = ''
    for k in keys:
        v = params[k]
        if v:
            text = text + str(v)

    return md5_encrypt(text + sign_key)


# 验证安全校验字符串是否相同
def check_sign(params, sign_key, sign):
    return gen_sign(params, sign_key) == sign
