# file: core/admin/ai_ops.py
# purpose: Admin 注册 OPS 模型，方便规则管理/通道配置/事件查看
from __future__ import annotations
from django.contrib import admin
from core.models.ai_ops import OpsAlertRule, OpsAlertChannel, OpsIncident


@admin.register(OpsAlertRule)
class OpsAlertRuleAdmin(admin.ModelAdmin):
    """规则 Admin：支持按租户过滤、按类型搜索。"""
    list_display = ("id", "tenant_id", "name", "type", "is_active", "updated_at")
    search_fields = ("tenant_id", "name", "type")
    list_filter = ("type", "is_active")


@admin.register(OpsAlertChannel)
class OpsAlertChannelAdmin(admin.ModelAdmin):
    """通道 Admin：查看通道健康状态与最近报错。"""
    list_display = ("id", "tenant_id", "name", "kind", "is_active", "updated_at")
    search_fields = ("tenant_id", "name", "kind")
    list_filter = ("kind", "is_active")


@admin.register(OpsIncident)
class OpsIncidentAdmin(admin.ModelAdmin):
    """事件 Admin：按严重级别与状态筛选；支持搜索 key。"""
    list_display = ("id", "tenant_id", "rule", "key", "severity", "status", "hit_count", "last_seen")
    search_fields = ("tenant_id", "key", "rule__name")
    list_filter = ("status", "severity")