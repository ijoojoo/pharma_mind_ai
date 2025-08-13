# file: core/views/ai/ops/channels.py
# purpose: 通道 CRUD 与测试发送
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.models.ai_ops import OpsAlertChannel
from core.ai.ops.notify import notify_incidents


class OpsChannelListCreateView(View):
    """GET 列表；POST 新建通道。"""

    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            rows = list(OpsAlertChannel.objects.filter(tenant_id=tenant_id).order_by("-updated_at"))
            items = [
                {"id": r.id, "name": r.name, "kind": r.kind, "config": r.config, "is_active": r.is_active, "updated_at": r.updated_at, "last_error": r.last_error}
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
            kind = (payload.get("kind") or "").strip()
            config = payload.get("config") or {}
            if not name or kind not in ("email", "webhook"):
                return fail("Invalid name/kind", status=400)
            obj = OpsAlertChannel.objects.create(tenant_id=tenant_id, name=name[:128], kind=kind, config=config)
            return ok({"id": obj.id})
        except Exception as e:
            return fail(str(e))


class OpsChannelDetailView(View):
    """PATCH 更新；DELETE 软删除；POST /test 测试发送。"""

    def patch(self, request: HttpRequest, cid: str):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            obj = OpsAlertChannel.objects.filter(id=cid, tenant_id=tenant_id).first()
            if not obj:
                return fail("Channel not found", status=404)
            if "name" in payload:
                obj.name = str(payload.get("name") or obj.name)[:128]
            if "is_active" in payload:
                obj.is_active = bool(payload.get("is_active"))
            if "config" in payload:
                obj.config = payload.get("config") or {}
            if "kind" in payload:
                obj.kind = str(payload.get("kind") or obj.kind)
            obj.save()
            return ok({"id": obj.id, "updated": True})
        except Exception as e:
            return fail(str(e))

    def delete(self, request: HttpRequest, cid: str):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            obj = OpsAlertChannel.objects.filter(id=cid, tenant_id=tenant_id).first()
            if not obj:
                return fail("Channel not found", status=404)
            obj.is_active = False
            obj.save(update_fields=["is_active"])
            return ok({"id": obj.id, "deleted": True})
        except Exception as e:
            return fail(str(e))

    def post(self, request: HttpRequest, cid: str, action: str):
        try:
            if action != "test":
                return fail("Unsupported action", status=400)
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            # 发送一条测试消息
            demo = [{"type": "test", "severity": "low", "group": {"demo": True}, "today": 0}]
            notify_incidents(tenant_id=tenant_id, items=demo)
            return ok({"tested": True})
        except Exception as e:
            return fail(str(e))