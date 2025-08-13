# file: core/admin/ai.py
# purpose: Django Admin 注册 AI 相关模型，便于运维查看与手工操作
from __future__ import annotations
from django.contrib import admin
from core.models.ai_billing import AiTenantTokenAccount, AiTokenTransaction
from core.models.ai_logging import AiChatSession, AiMessage, AiRun, AiCallLog
from core.models.ai_settings import AiTenantDefaultModel, AiModelPreference


@admin.register(AiTenantTokenAccount)
class AiTenantTokenAccountAdmin(admin.ModelAdmin):
    list_display = ("tenant_id", "plan", "token_balance", "soft_limit", "hard_limit", "status", "updated_at")
    search_fields = ("tenant_id", "plan")
    list_filter = ("status",)


@admin.register(AiTokenTransaction)
class AiTokenTransactionAdmin(admin.ModelAdmin):
    list_display = ("tenant_id", "change", "reason", "related_run_id", "created_at")
    search_fields = ("tenant_id", "reason", "related_run_id")
    date_hierarchy = "created_at"


@admin.register(AiChatSession)
class AiChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant_id", "user_id", "agent", "title", "status", "updated_at")
    search_fields = ("tenant_id", "user_id", "title")
    list_filter = ("agent", "status")


@admin.register(AiMessage)
class AiMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "tokens_in", "tokens_out", "created_at")
    search_fields = ("session__tenant_id", "session__user_id", "content")
    date_hierarchy = "created_at"


@admin.register(AiRun)
class AiRunAdmin(admin.ModelAdmin):
    list_display = ("trace_id", "tenant_id", "agent", "session", "latency_ms", "created_at")
    search_fields = ("tenant_id", "trace_id", "agent")
    date_hierarchy = "created_at"


@admin.register(AiCallLog)
class AiCallLogAdmin(admin.ModelAdmin):
    list_display = ("run", "provider", "model", "tokens_in", "tokens_out", "latency_ms", "created_at")
    search_fields = ("provider", "model", "run__trace_id")
    date_hierarchy = "created_at"


@admin.register(AiTenantDefaultModel)
class AiTenantDefaultModelAdmin(admin.ModelAdmin):
    list_display = ("tenant_id", "provider_key", "model_name", "is_active", "updated_at")
    search_fields = ("tenant_id", "provider_key", "model_name")
    list_filter = ("is_active",)


@admin.register(AiModelPreference)
class AiModelPreferenceAdmin(admin.ModelAdmin):
    list_display = ("tenant_id", "user_id", "provider_key", "model_name", "is_active", "updated_at")
    search_fields = ("tenant_id", "user_id", "provider_key", "model_name")
    list_filter = ("is_active",)