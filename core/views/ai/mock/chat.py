# file: core/views/ai/mock/chat.py
# purpose: Mock Chat 接口：不调用 LLM，返回可预测的固定结构，便于前端联调
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json


class MockChatView(View):
    """POST /api/ai/mock/chat/ → 接收 {messages:[...]}，回显最后一条用户消息并附上固定 AI 回复。"""

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            messages = payload.get("messages") or []
            last_user = ""
            for m in reversed(messages):
                if str(m.get("role")) == "user":
                    last_user = str(m.get("content") or "")
                    break
            reply = f"[MOCK AI] 我已收到你的消息：{last_user[:200]}"
            return ok({
                "reply": reply,
                "echo": messages[-3:],
                "tokens_spent": 0,
            })
        except Exception as e:
            return fail(str(e))

