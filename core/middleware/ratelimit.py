# file: core/middleware/ratelimit.py
# purpose: 简易限流中间件（按租户/用户）。默认限制：租户 60 req/60s，用户 30 req/60s。仅对 /api/ai/ 路径生效。
from __future__ import annotations
import time
from typing import Callable
from django.http import JsonResponse, HttpRequest
from django.core.cache import cache
from django.conf import settings


class RateLimitMiddleware:
    """在 /api/ai/ 路径上对请求进行速率限制（租户/用户两个维度）。

    配置：settings.AI_RATE_LIMIT = {
        "tenant_limit": 60,  # 租户窗口内最大请求数
        "user_limit": 30,    # 用户窗口内最大请求数
        "window": 60,        # 秒
    }
    若未配置，则采用上述默认值。
    """

    def __init__(self, get_response: Callable):
        """初始化中间件：读取并缓存速率限制配置。"""
        self.get_response = get_response
        cfg = getattr(settings, "AI_RATE_LIMIT", {}) or {}
        self.tenant_limit = int(cfg.get("tenant_limit", 60))
        self.user_limit = int(cfg.get("user_limit", 30))
        self.window = int(cfg.get("window", 60))  # seconds

    def __call__(self, request: HttpRequest):
        """处理请求：超过阈值返回 429，并附带剩余额度头部。"""
        path = request.path or ""
        if "/api/ai/" not in path:
            return self.get_response(request)
        tenant_id = request.headers.get("X-Tenant-Id") or getattr(request, "tenant_id", None) or "_"
        user_id = getattr(request, "user_id", None) or request.headers.get("X-User-Id") or "_"
        now = int(time.time())
        bucket = now // self.window
        # 租户维度
        tkey = f"ai:rl:t:{tenant_id}:{bucket}"
        tcount = cache.get(tkey) or 0
        if tcount >= self.tenant_limit:
            return self._reject(self.tenant_limit, 0)
        cache.add(tkey, 0, timeout=self.window)
        cache.incr(tkey)
        # 用户维度
        ukey = f"ai:rl:u:{tenant_id}:{user_id}:{bucket}"
        ucount = cache.get(ukey) or 0
        if ucount >= self.user_limit:
            return self._reject(self.user_limit, 0)
        cache.add(ukey, 0, timeout=self.window)
        rem = max(0, self.user_limit - ucount - 1)
        resp = self.get_response(request)
        if hasattr(resp, "__setitem__"):
            resp["X-RateLimit-Remaining"] = str(rem)
        cache.incr(ukey)
        return resp

    @staticmethod
    def _reject(limit: int, retry_after: int) -> JsonResponse:
        """构造 429 响应。"""
        data = {"detail": "Rate limit exceeded", "limit": limit}
        resp = JsonResponse(data, status=429)
        if retry_after:
            resp["Retry-After"] = str(retry_after)
        return resp
