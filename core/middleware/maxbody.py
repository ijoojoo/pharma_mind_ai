# file: core/middleware/maxbody.py
# purpose: 请求体大小限制中间件（413 Payload Too Large）——仅对 /api/ai/ 生效
# 配置：settings.AI_MAX_REQUEST_BYTES（默认 1MB）
from __future__ import annotations
from typing import Callable
from django.http import HttpRequest, JsonResponse
from django.conf import settings


class MaxBodyMiddleware:
    """限制 JSON 请求体的最大大小，避免误传大文件导致内存或性能问题。"""

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.limit = int(getattr(settings, "AI_MAX_REQUEST_BYTES", 1 * 1024 * 1024))

    def __call__(self, request: HttpRequest):
        path = request.path or ""
        if not path.startswith("/api/ai/"):
            return self.get_response(request)
        clen = request.META.get("CONTENT_LENGTH")
        if clen:
            try:
                if int(clen) > self.limit:
                    return self._reject()
            except Exception:
                pass
        # 再保险：实际读到的 body 长度
        body = request.body or b""
        if len(body) > self.limit:
            return self._reject()
        return self.get_response(request)

    def _reject(self) -> JsonResponse:
        return JsonResponse({"success": False, "error": {"code": "bad_request", "message": "payload too large"}}, status=413)

