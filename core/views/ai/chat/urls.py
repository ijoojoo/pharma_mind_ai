# file: core/views/ai/chat/urls.py
# purpose: Chat 路由（包含会话与消息）；修复之前遗漏 session 的问题
from __future__ import annotations
from django.urls import path
from .message import ChatMessageView
from .session import ChatSessionView, ChatSessionDetailView

urlpatterns = [
    path("message/", ChatMessageView.as_view(), name="ai_chat_message"),
    path("session/", ChatSessionView.as_view(), name="ai_chat_session"),
    path("session/<str:session_id>/", ChatSessionDetailView.as_view(), name="ai_chat_session_detail"),
]
