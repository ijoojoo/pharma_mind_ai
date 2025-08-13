# file: core/middleware/tenant.py
# purpose: 从请求头注入 tenant_id 到 request.tenant_id，便于下游统一读取
from __future__ import annotations
from typing import Callable
from django.http import HttpRequest


class TenantMiddleware:
    """读取 X-Tenant-Id 并注入到 request.tenant_id，便于后续视图/服务统一读取。"""

    def __init__(self, get_response: Callable):
        """保存下游响应回调。"""
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        """在请求对象上挂载 tenant_id 字段，然后继续处理。"""
        request.tenant_id = request.headers.get("X-Tenant-Id") or None
        return self.get_response(request)
