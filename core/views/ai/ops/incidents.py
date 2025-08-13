# file: core/views/ai/ops/incidents.py
# purpose: 事件列表与状态流转（ack/close）
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.models.ai_ops import OpsIncident


class OpsIncidentListView(View):
    """GET 列表；支持按状态/严重度过滤。"""

    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            status = (request.GET.get("status") or "").strip()
            severity = (request.GET.get("severity") or "").strip()
            qs = OpsIncident.objects.filter(tenant_id=tenant_id).order_by("-last_seen")
            if status:
                qs = qs.filter(status=status)
            if severity:
                qs = qs.filter(severity=severity)
            rows = list(qs[:500])
            items = [
                {"id": it.id, "rule_id": getattr(it.rule, "id", None), "key": it.key, "severity": it.severity, "status": it.status, "hit_count": it.hit_count, "last_seen": it.last_seen, "payload": it.payload}
                for it in rows
            ]
            return ok({"items": items, "count": len(items)})
        except Exception as e:
            return fail(str(e))


class OpsIncidentActionView(View):
    """POST 动作：ack/close/reopen。"""

    def post(self, request: HttpRequest, iid: str, action: str):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            it = OpsIncident.objects.filter(id=iid, tenant_id=tenant_id).first()
            if not it:
                return fail("Incident not found", status=404)
            if action == "ack":
                it.status = "ack"
            elif action == "close":
                it.status = "closed"
            elif action == "reopen":
                it.status = "open"
            else:
                return fail("Unsupported action", status=400)
            it.save(update_fields=["status"])
            return ok({"id": it.id, "status": it.status})
        except Exception as e:
            return fail(str(e))
