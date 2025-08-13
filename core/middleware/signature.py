# file: core/middleware/signature.py
# purpose: API 签名校验中间件（防重放/防篡改）——仅对 /api/ai/ 生效
# 说明：
# - 通过 HMAC-SHA256 校验：X-Api-Key + X-Timestamp + X-Nonce + 请求方法/路径/Body-SHA256
# - 抗重放：在允许的时间偏差内校验 nonce 未被使用（缓存去重）
# - 配置（settings.AI_SIGNING）：
#   AI_SIGNING = {
#       "enabled": True,
#       "clock_skew": 300,          # 允许的秒级时间偏差
#       "nonce_ttl": 600,            # nonce 存活时间（秒）
#       "keys": {                    # 客户端分配的 api_key → secret / tenant 绑定
#           "demo-key": {"secret": "demo-secret", "tenant_id": "demo-tenant"},
#           "*": {"secret": "public-secret"},     # 通配（可选）
#       },
#   }
from __future__ import annotations
import hashlib
import hmac
import time
from typing import Callable, Dict, Any
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.core.cache import cache
from django.conf import settings


class SignatureAuthMiddleware:
    """HMAC 签名校验，仅作用于 /api/ai/ 路径。
    头部要求：
      - X-Api-Key      客户端分配的 key
      - X-Timestamp    发起时间（epoch 秒）
      - X-Nonce        客户端随机串（建议 UUID）
      - X-Signature    HMAC hexdigest
    Canonical String:
      method + "\n" + path + "\n" + timestamp + "\n" + nonce + "\n" + sha256(body)
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.cfg = getattr(settings, "AI_SIGNING", {}) or {}
        self.enabled: bool = bool(self.cfg.get("enabled", False))
        self.clock_skew: int = int(self.cfg.get("clock_skew", 300))
        self.nonce_ttl: int = int(self.cfg.get("nonce_ttl", 600))
        self.keys: Dict[str, Dict[str, Any]] = dict(self.cfg.get("keys", {}))

    def __call__(self, request: HttpRequest):
        if not self.enabled or not (request.path or "").startswith("/api/ai/"):
            return self.get_response(request)
        try:
            return self._handle(request)
        except Exception as e:
            return self._reject(401, code="unauthorized", msg=str(e))

    # ---- core ----
    def _handle(self, request: HttpRequest) -> HttpResponse:
        api_key = request.headers.get("X-Api-Key")
        ts = request.headers.get("X-Timestamp")
        nonce = request.headers.get("X-Nonce")
        sig = request.headers.get("X-Signature")
        if not (api_key and ts and nonce and sig):
            return self._reject(401, code="unauthorized", msg="missing signature headers")
        try:
            ts_i = int(ts)
        except Exception:
            return self._reject(401, code="unauthorized", msg="invalid timestamp")
        now = int(time.time())
        if abs(now - ts_i) > self.clock_skew:
            return self._reject(401, code="unauthorized", msg="timestamp out of skew")
        # 查找 secret
        meta = self.keys.get(api_key) or self.keys.get("*")
        if not (meta and meta.get("secret")):
            return self._reject(401, code="unauthorized", msg="unknown api key")
        secret = str(meta["secret"]).encode("utf-8")
        # 计算 body 摘要
        body = request.body or b""
        body_sha = hashlib.sha256(body).hexdigest()
        canonical = f"{request.method.upper()}\n{request.path}\n{ts}\n{nonce}\n{body_sha}".encode("utf-8")
        calc = hmac.new(secret, canonical, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, sig):
            return self._reject(401, code="unauthorized", msg="bad signature")
        # 抗重放（nonce）
        nkey = f"ai:sig:nonce:{api_key}:{nonce}"
        if cache.add(nkey, 1, timeout=self.nonce_ttl) is False:
            return self._reject(409, code="unauthorized", msg="nonce replayed")
        # 若配置了 tenant 绑定，校验 X-Tenant-Id
        bound_tid = str(meta.get("tenant_id") or "")
        if bound_tid:
            req_tid = request.headers.get("X-Tenant-Id") or getattr(request, "tenant_id", None)
            if req_tid != bound_tid:
                return self._reject(403, code="forbidden", msg="tenant mismatch for api key")
        return self.get_response(request)

    # ---- helpers ----
    def _reject(self, status: int, *, code: str, msg: str) -> JsonResponse:
        return JsonResponse({"success": False, "error": {"code": code, "message": msg}}, status=status)

