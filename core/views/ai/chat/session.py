# file: core/views/ai/chat/session.py
# purpose: Chat 会话管理（列表/创建/详情/修改/归档）；与 ChatMessageView 协同使用
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from django.utils import timezone
from core.views.utils import ok, fail, get_json, get_enterprise
from core.models.ai_logging import AiChatSession, AiMessage


class ChatSessionView(View):
    """/api/ai/chat/session/
    GET  : 列表（按 tenant，支持状态与分页）
    POST : 新建会话（可指定 title/agent）
    """

    def get(self, request: HttpRequest):
        try:
            ent = get_enterprise(request, required=True)
            tenant_id = ent["tenant_id"]
            status = (request.GET.get("status") or "").strip()
            limit = int(request.GET.get("limit", 20))
            offset = int(request.GET.get("offset", 0))
            qs = AiChatSession.objects.filter(tenant_id=tenant_id).order_by("-updated_at")
            if status:
                qs = qs.filter(status=status)
            total = qs.count()
            rows = list(qs[offset: offset + max(1, min(limit, 100))])
            items = [
                {
                    "id": str(r.id),
                    "tenant_id": r.tenant_id,
                    "user_id": getattr(r, "user_id", None),
                    "agent": getattr(r, "agent", None),
                    "title": getattr(r, "title", ""),
                    "status": getattr(r, "status", "active"),
                    "updated_at": r.updated_at,
                }
                for r in rows
            ]
            return ok({"items": items, "total": total, "offset": offset, "limit": limit})
        except Exception as e:
            return fail(str(e))

    def post(self, request: HttpRequest):
        try:
            ent = get_enterprise(request, required=True)
            tenant_id = ent["tenant_id"]
            user_id = ent.get("user_id") or ""
            payload = get_json(request)
            title = (payload.get("title") or "新会话").strip() or "新会话"
            agent = (payload.get("agent") or "chat").strip() or "chat"
            obj = AiChatSession.objects.create(
                tenant_id=tenant_id,
                user_id=user_id,
                agent=agent,
                title=title[:100],
                status="active",
                updated_at=timezone.now(),
            )
            return ok({"id": str(obj.id), "title": obj.title, "agent": obj.agent, "status": obj.status})
        except Exception as e:
            return fail(str(e))


class ChatSessionDetailView(View):
    """/api/ai/chat/session/<id>/
    GET    : 详情（可带最近消息）
    PATCH  : 修改标题/状态（支持 {title, status}）
    DELETE : 归档（将 status=archived；若模型无该字段，可改为删除）
    """

    def get(self, request: HttpRequest, session_id: str):
        try:
            ent = get_enterprise(request, required=True)
            tenant_id = ent["tenant_id"]
            obj = AiChatSession.objects.filter(id=session_id, tenant_id=tenant_id).first()
            if not obj:
                return fail("Session not found", status=404)
            # 最近消息
            limit = int(request.GET.get("limit", 50))
            msgs = AiMessage.objects.filter(session=obj).order_by("-created_at")[: max(1, min(limit, 200))]
            messages = [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "tokens_in": m.tokens_in,
                    "tokens_out": m.tokens_out,
                    "created_at": m.created_at,
                }
                for m in msgs
            ]
            data = {
                "id": str(obj.id),
                "tenant_id": obj.tenant_id,
                "user_id": getattr(obj, "user_id", None),
                "agent": getattr(obj, "agent", None),
                "title": getattr(obj, "title", ""),
                "status": getattr(obj, "status", "active"),
                "updated_at": obj.updated_at,
                "messages": list(reversed(messages)),  # 时间正序
            }
            return ok(data)
        except Exception as e:
            return fail(str(e))

    def patch(self, request: HttpRequest, session_id: str):
        try:
            ent = get_enterprise(request, required=True)
            tenant_id = ent["tenant_id"]
            obj = AiChatSession.objects.filter(id=session_id, tenant_id=tenant_id).first()
            if not obj:
                return fail("Session not found", status=404)
            payload = get_json(request)
            changed = False
            title = payload.get("title")
            status = payload.get("status")
            if title is not None:
                obj.title = (str(title).strip() or obj.title)[:100]
                changed = True
            if status is not None:
                obj.status = str(status)
                changed = True
            if changed:
                obj.updated_at = timezone.now()
                obj.save(update_fields=["title", "status", "updated_at"])
            return ok({"id": str(obj.id), "title": obj.title, "status": obj.status})
        except Exception as e:
            return fail(str(e))

    def delete(self, request: HttpRequest, session_id: str):
        try:
            ent = get_enterprise(request, required=True)
            tenant_id = ent["tenant_id"]
            obj = AiChatSession.objects.filter(id=session_id, tenant_id=tenant_id).first()
            if not obj:
                return fail("Session not found", status=404)
            # 归档而非硬删除
            if hasattr(obj, "status"):
                obj.status = "archived"
                obj.updated_at = timezone.now()
                obj.save(update_fields=["status", "updated_at"])
            else:
                obj.delete()
            return ok({"id": str(obj.id), "archived": True})
        except Exception as e:
            return fail(str(e))
