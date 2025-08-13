# file: core/views/ai/ops/anomaly.py
# purpose: 异常检测占位（MVP：仅回传未实现），后续接入规则/统计学习
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json


class OpsAnomalyView(View):
    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            return ok({"status": "not_implemented", "message": "异常检测尚未实现，后续将接入规则与统计阈值。"})
        except Exception as e:
            return fail(str(e))