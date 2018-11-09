
from __future__ import absolute_import

import base64
from Crypto.Cipher import AES


class SecurityService:
    def __init__(self):
        # 加解密秘钥
        self.key = "PnCEWvzhoH6Yt2aP"
        # 加盐因子
        self.iv = "1237635217384736"
        self.mode = AES.MODE_CBC

    def check16(self, text):
        """
        检查text是不是16的倍数，不是那就用空格补足为16的倍数。

        :param text: 待加密的原文。
        :returns: 待加密的原文字节。
        :raises keyError: raises an exception
        """
        byts = bytes(text, encoding="utf-8")
        BS = 16
        count = len(byts)
        if(count % BS != 0):
            add = BS - (count % BS)
            byts = byts + (b' ' * add)
        return byts

    def encrypt(self, text):
        """
        加密方法。

        :param text: 待加密的原文, str类型。
        :returns: 通过AES加密算法加密后的内容，加密返回内容通过Base64编码。
        """
        # 初始化加密器
        aes = AES.new(self.check16(self.key), self.mode, self.check16(self.iv))
        # 先进行aes加密
        encrypt_aes = aes.encrypt(self.check16(text))
        # 用base64转成字符串形式
        encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='utf-8')
        return encrypted_text

    def decrypt(self, text):
        """
        解密方法。

        :param text: 待解密的内容。
        :returns: 返回解密后的文本。
        """
        # 用base64解码
        base64_decrypted = base64.decodebytes(text.encode(encoding='utf-8'))
        # 初始化加密器
        aes = AES.new(self.check16(self.key), self.mode, self.check16(self.iv))
        decrypted_text = str(aes.decrypt(base64_decrypted), encoding='utf-8')
        # 执行解密密并转码返回str
        return decrypted_text.strip()
