# file: core/views/ai/ops/rules.py
# purpose: 规则 CRUD：列出/创建/更新/删除（软删除：is_active=false）
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.models.ai_ops import OpsAlertRule


class OpsRuleListCreateView(View):
    """GET 列表；POST 新建。"""

    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            rows = list(OpsAlertRule.objects.filter(tenant_id=tenant_id).order_by("-updated_at"))
            items = [
                {"id": r.id, "name": r.name, "type": r.type, "config": r.config, "is_active": r.is_active, "updated_at": r.updated_at}
                for r in rows
            ]
            return ok({"items": items})
        except Exception as e:
            return fail(str(e))

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            name = (payload.get("name") or "").strip()
            rtype = (payload.get("type") or "").strip()
            config = payload.get("config") or {}
            if not name or not rtype:
                return fail("Missing name/type", status=400)
            obj = OpsAlertRule.objects.create(tenant_id=tenant_id, name=name[:128], type=rtype[:32], config=config)
            return ok({"id": obj.id})
        except Exception as e:
            return fail(str(e))


class OpsRuleDetailView(View):
    """PATCH 部分更新；DELETE 软删除（置 is_active=false）。"""

    def patch(self, request: HttpRequest, rid: str):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            obj = OpsAlertRule.objects.filter(id=rid, tenant_id=tenant_id).first()
            if not obj:
                return fail("Rule not found", status=404)
            if "name" in payload:
                obj.name = str(payload.get("name") or obj.name)[:128]
            if "type" in payload:
                obj.type = str(payload.get("type") or obj.type)[:32]
            if "config" in payload:
                obj.config = payload.get("config") or {}
            if "is_active" in payload:
                obj.is_active = bool(payload.get("is_active"))
            obj.save()
            return ok({"id": obj.id, "updated": True})
        except Exception as e:
            return fail(str(e))

    def delete(self, request: HttpRequest, rid: str):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            obj = OpsAlertRule.objects.filter(id=rid, tenant_id=tenant_id).first()
            if not obj:
                return fail("Rule not found", status=404)
            obj.is_active = False
            obj.save(update_fields=["is_active"])
            return ok({"id": obj.id, "deleted": True})
        except Exception as e:
            return fail(str(e))