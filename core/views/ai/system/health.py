# file: core/views/ai/system/health.py
# purpose: 健康检查/自检视图：GET /api/ai/system/health/ 与 /api/ai/system/selfcheck/
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail
from core.ai.diagnostics import run_health, run_selfcheck


class AiHealthView(View):
    """返回系统级健康检查（不含租户维度）。"""

    def get(self, request: HttpRequest):
        try:
            rep = run_health()
            return ok(rep.to_dict())
        except Exception as e:
            return fail(str(e))


class AiSelfcheckView(View):
    """结合租户上下文的自检（需要 X-Tenant-Id）。"""

    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            rep = run_selfcheck(tenant_id=tenant_id)
            return ok(rep.to_dict())
        except Exception as e:
            return fail(str(e))