# file: scripts/examples/python/sign_request.py
# purpose: 客户端计算签名的示例脚本（Python）；生成请求头用于调用受保护的 /api/ai/ 接口
from __future__ import annotations
import hashlib
import hmac
import json
import time
import uuid
import requests  # 仅用于示例发请求；若未安装可把 PRINT_ONLY 改为 True

API_BASE = "http://127.0.0.1:8000"
API_PATH = "/api/ai/system/health/"   # 例子：GET 无 body
API_KEY = "demo-key"
API_SECRET = "demo-secret"  # 与服务器 settings.AI_SIGNING.keys[API_KEY].secret 保持一致
TENANT_ID = "demo-tenant"    # 如服务器对 key 绑定了 tenant_id，这里需匹配
PRINT_ONLY = False


def sign(method: str, path: str, body: bytes, key: str, secret: str) -> dict:
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex
    body_sha = hashlib.sha256(body or b"").hexdigest()
    canonical = f"{method.upper()}\n{path}\n{ts}\n{nonce}\n{body_sha}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    return {
        "X-Api-Key": key,
        "X-Timestamp": ts,
        "X-Nonce": nonce,
        "X-Signature": sig,
    }


if __name__ == "__main__":
    method = "GET"
    body = b""
    headers = sign(method, API_PATH, body, API_KEY, API_SECRET)
    headers["Accept"] = "application/json"
    headers["X-Tenant-Id"] = TENANT_ID
    url = API_BASE + API_PATH
    print("# request")
    print(method, url)
    print(headers)
    if not PRINT_ONLY:
        resp = requests.get(url, headers=headers, timeout=10)
        print("# response", resp.status_code)
        print(resp.text)

