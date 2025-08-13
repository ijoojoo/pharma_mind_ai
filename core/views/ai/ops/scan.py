# file: core/views/ai/ops/scan.py
# purpose: 手动触发一次扫描（可用于调试/定时任务触发器）
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.ops.runner import run_ops_scan
from core.ai.ops.notify import notify_incidents


class OpsScanView(View):
    """POST {window?, extra_rules?, notify?}：触发一次扫描，并可选地发送告警。"""

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            window = payload.get("window") or {}
            extra = payload.get("extra_rules") or []
            notify = bool(payload.get("notify", True))
            items = run_ops_scan(tenant_id=tenant_id, window=window, extra_rules=extra)
            if notify and items:
                notify_incidents(tenant_id=tenant_id, items=items)
            return ok({"items": items, "count": len(items)})
        except Exception as e:
            return fail(str(e))
