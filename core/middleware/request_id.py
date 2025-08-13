# file: core/middleware/request_id.py
# purpose: 统一请求 ID 管理（从头读取或生成），并注入到日志上下文与响应头
from __future__ import annotations
import uuid
from typing import Callable
from django.http import HttpRequest

# 使用 contextvars 保存 request_id，供 JSON 日志 Formatter 读取
import contextvars
REQUEST_ID_CTX = contextvars.ContextVar("request_id", default="-")


class RequestIdMiddleware:
    """确保所有 /api/ai/ 请求都有 X-Request-Id。"""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        REQUEST_ID_CTX.set(rid)
        response = self.get_response(request)
        try:
            response["X-Request-Id"] = rid
        except Exception:
            pass
        return response


