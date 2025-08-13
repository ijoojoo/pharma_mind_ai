# file: core/views/ai/chat/message.py
# purpose: Chat 消息接口（POST）— 解析租户/用户与 session → Orchestrator.chat_once → 统一计费与日志
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from django.utils import timezone
from core.views.utils import ok, fail, get_json, get_enterprise
from core.ai.orchestrator import Orchestrator
from core.ai.billing import InsufficientBalance, InsufficientTokens, AccountSuspended
from core.models.ai_logging import AiChatSession


class ChatMessageView(View):
    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            ent = get_enterprise(request, required=True)
            tenant_id = ent.get("tenant_id")
            user_id = ent.get("user_id")
            message = (payload.get("message") or payload.get("text") or "").strip()
            if not message:
                return fail("Missing message", status=400)

            # 1) 解析/创建会话
            session_id = payload.get("session_id") or request.GET.get("session_id")
            session = None
            if session_id:
                session = AiChatSession.objects.filter(id=session_id, tenant_id=tenant_id).first()
            if not session:
                session = AiChatSession.objects.create(
                    tenant_id=tenant_id,
                    user_id=user_id or "",
                    agent=str(payload.get("agent") or "chat"),
                    title=(message[:20] or "新会话"),
                    status="active",
                    updated_at=timezone.now(),
                )

            # 2) 调用编排器（内部已做预授权、审计与结算）
            o = Orchestrator(tenant_id=tenant_id, agent=session.agent)
            result = o.chat_once(session=session, user_message=message)

            # 3) 成功响应
            return ok({
                "session_id": str(session.id),
                "trace_id": result.get("trace_id"),
                "content": result.get("content"),
                "tokens_spent": result.get("spent"),
            })

        except (InsufficientTokens, InsufficientBalance) as e:
            return fail(str(e) or "Insufficient balance", status=402, code="insufficient_tokens")
        except AccountSuspended as e:
            return fail(str(e) or "Account suspended", status=403, code="account_suspended")
        except Exception as e:
            # 其余异常统一 500
            return fail(str(e), status=500)