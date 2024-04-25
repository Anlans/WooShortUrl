import string
import random
import base64


def generate_short_url(size=7) -> str:
    letters = string.ascii_letters + string.digits
    short_tag = ''.join(random.choice(letters) for i in range(size))
    return short_tag


def generate_short_url_with_base64(identifier: int) -> str:
    # 将数字转换为二进制字节
    binary_data = identifier.to_bytes((identifier.bit_length() + 7) // 8, 'big')
    # 编码为base64并解码为ASCII字符串，去除base64编码后常见的'='填充符
    short_tag = base64.urlsafe_b64encode(binary_data).decode('utf-8').rstrip('=')
    return short_tag


# 将短链接转换为原始id
def decode_short_url(short_tag: str) -> int:
    # 首先确保字符串长度是4的倍数，因为原始编码中可能移除了'='
    while len(short_tag) % 4 != 0:
        short_tag += '='
    # Base64 解码
    binary_data = base64.urlsafe_b64decode(short_tag)
    # 二进制数转整数
    identifier = int.from_bytes(binary_data, 'big')

    return identifier

