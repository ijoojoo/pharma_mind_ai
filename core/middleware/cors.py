# file: core/middleware/cors.py
# purpose: 轻量 CORS 中间件（仅对 /api/ai/ 路径生效）；无需第三方库，支持自定义来源/方法/头部/凭证
from __future__ import annotations
from typing import Callable, Iterable
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings


class CorsMiddleware:
    """为 /api/ai/ 开头的请求追加 CORS 头；处理 OPTIONS 预检请求。
    配置项（settings）：
      AI_CORS = {
        "allow_origins": ["http://localhost:3000", "http://127.0.0.1:3000", "*"],
        "allow_methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Tenant-Id", "X-User-Id"],
        "expose_headers": ["X-RateLimit-Remaining"],
        "allow_credentials": True,
        "max_age": 600,
      }
    若未设置，按以上默认值回退。
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        cfg = getattr(settings, "AI_CORS", {}) or {}
        self.allow_origins = list(cfg.get("allow_origins") or ["*"])
        self.allow_methods = list(cfg.get("allow_methods") or ["GET", "POST", "OPTIONS"])
        self.allow_headers = list(cfg.get("allow_headers") or ["Content-Type", "Authorization", "X-Tenant-Id", "X-User-Id"]) 
        self.expose_headers = list(cfg.get("expose_headers") or ["X-RateLimit-Remaining"]) 
        self.allow_credentials = bool(cfg.get("allow_credentials", True))
        self.max_age = int(cfg.get("max_age", 600))

    def __call__(self, request: HttpRequest):
        path = request.path or ""
        if not path.startswith("/api/ai/"):
            return self.get_response(request)

        # 预检请求：直接返回 204 并附带 CORS 头
        if request.method == "OPTIONS":
            resp = HttpResponse(status=204)
            return self._apply(resp, request)

        # 正常请求：先下游处理，再补充 CORS 头
        resp = self.get_response(request)
        if isinstance(resp, HttpResponse):
            return self._apply(resp, request)
        return resp

    # ---- helpers ----
    def _apply(self, resp: HttpResponse, request: HttpRequest) -> HttpResponse:
        origin = request.headers.get("Origin") or "*"
        allow_origin = origin if ("*" in self.allow_origins or origin in self.allow_origins) else ""
        resp["Access-Control-Allow-Origin"] = allow_origin or "*"
        if self.allow_credentials:
            resp["Access-Control-Allow-Credentials"] = "true"
        resp["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        resp["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        if self.expose_headers:
            resp["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
        if self.max_age:
            resp["Access-Control-Max-Age"] = str(self.max_age)
        return resp
