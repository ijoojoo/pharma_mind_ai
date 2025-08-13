# file: core/middleware/auth.py
# purpose: 可选的 API Key 鉴权中间件（对 /api/ai/ 生效）；默认关闭，通过 settings.AI_REQUIRE_AUTH 控制
from __future__ import annotations
from typing import Callable, Dict, List
from django.http import JsonResponse, HttpRequest
from django.conf import settings


class ApiKeyAuthMiddleware:
    """对 /api/ai/ 路径启用可选的 API Key 鉴权。

    行为说明：
    - 若 settings.AI_REQUIRE_AUTH 为 False（默认），直接放行（完全不影响现有接口）。
    - 若为 True，则要求请求头包含：
        * X-Tenant-Id: 租户标识
        * X-Api-Key  : 与 settings.AI_API_KEYS 中该租户配置匹配
      否则返回 401。
    - settings.AI_API_KEYS 支持两种形式：
        {"tenantA": "key123", "tenantB": ["k1", "k2"]}
    """

    def __init__(self, get_response: Callable):
        """初始化中间件并缓存配置。"""
        self.get_response = get_response
        self._require = bool(getattr(settings, "AI_REQUIRE_AUTH", False))
        self._keymap: Dict[str, List[str]] = {}
        raw = getattr(settings, "AI_API_KEYS", {}) or {}
        for k, v in raw.items():
            if isinstance(v, (list, tuple)):
                self._keymap[str(k)] = [str(x) for x in v]
            elif v is None:
                self._keymap[str(k)] = []
            else:
                self._keymap[str(k)] = [str(v)]

    def __call__(self, request: HttpRequest):
        """处理请求：在 /api/ai/ 路径上执行 API Key 校验或放行。"""
        # 非 AI 路径不处理
        if "/api/ai/" not in (request.path or ""):
            return self.get_response(request)
        # 未开启鉴权 → 放行
        if not self._require:
            return self.get_response(request)
        # 开启鉴权 → 校验头
        tenant_id = request.headers.get("X-Tenant-Id") or getattr(request, "tenant_id", None)
        api_key = request.headers.get("X-Api-Key")
        if not tenant_id or not api_key:
            return self._unauthorized("Missing X-Tenant-Id or X-Api-Key")
        allowed = self._keymap.get(str(tenant_id), [])
        if allowed and api_key in allowed:
            return self.get_response(request)
        return self._unauthorized("Invalid api key for tenant")

    @staticmethod
    def _unauthorized(msg: str) -> JsonResponse:
        """构造 401 响应。"""
        return JsonResponse({"success": False, "error": {"code": "unauthorized", "message": msg}}, status=401)