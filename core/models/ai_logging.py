# file: core/models/ai_logging.py
# purpose: AI 会话、消息、运行与底层调用日志，支持全链路审计
from __future__ import annotations
from django.db import models


class AiChatSession(models.Model):
    tenant_id = models.CharField(max_length=64, db_index=True)
    user_id = models.CharField(max_length=64, db_index=True)
    agent = models.CharField(max_length=64, default="default")
    title = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=16, default="open")  # open/closed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_chat_session"
        indexes = [models.Index(fields=["tenant_id", "agent", "updated_at"])]


class AiMessage(models.Model):
    session = models.ForeignKey(AiChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16)  # user/assistant/system/tool
    content = models.TextField()
    tool_calls = models.JSONField(default=list, blank=True)
    tokens_in = models.IntegerField(default=0)
    tokens_out = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_message"
        indexes = [models.Index(fields=["session", "created_at"])]


class AiRun(models.Model):
    trace_id = models.CharField(max_length=64, db_index=True, unique=True)
    tenant_id = models.CharField(max_length=64, db_index=True)
    agent = models.CharField(max_length=64)
    session = models.ForeignKey(AiChatSession, null=True, blank=True, on_delete=models.SET_NULL)
    inputs = models.JSONField(default=dict)
    outputs = models.JSONField(default=dict)
    latency_ms = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_run"
        indexes = [models.Index(fields=["tenant_id", "created_at"])]


class AiCallLog(models.Model):
    run = models.ForeignKey(AiRun, on_delete=models.CASCADE, related_name="calls")
    provider = models.CharField(max_length=64)
    model = models.CharField(max_length=128)
    tokens_in = models.IntegerField(default=0)
    tokens_out = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    error = models.CharField(max_length=255, blank=True, default="")
    raw = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_call_log"
        indexes = [models.Index(fields=["model", "created_at"])]