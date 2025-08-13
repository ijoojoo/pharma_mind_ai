# file: core/models/ai_ops.py
# purpose: OPS 告警相关 ORM 模型：规则、通道、事件/工单；支持多租户隔离与基础生命周期管理
from __future__ import annotations
from django.db import models
from django.utils import timezone


class OpsAlertRule(models.Model):
    """一条异常检测规则（可启停）。
    - 与 core.ai.ops.anomaly_rules.Rule 对应；type 取值如：sales_drop/stockout/price_spike
    - config: 规则参数（JSON），如 {"threshold_pct":30, "lookback":7, "group_by":["store_id","product_id"]}
    """
    tenant_id = models.CharField(max_length=64, db_index=True, help_text="多租户隔离标识")
    name = models.CharField(max_length=128, help_text="规则名称")
    type = models.CharField(max_length=32, help_text="规则类型：sales_drop/stockout/price_spike")
    config = models.JSONField(default=dict, blank=True, help_text="规则参数 JSON")
    is_active = models.BooleanField(default=True, help_text="启用/停用")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_ops_alert_rule"
        indexes = [models.Index(fields=["tenant_id", "is_active", "type"])]

    def __str__(self) -> str:
        """返回易读的规则名称。"""
        return f"Rule<{self.id}:{self.name}>"


class OpsAlertChannel(models.Model):
    """告警通道（邮箱/Webhook）。
    - kind: email|webhook
    - config: email {"to":[...]}；webhook {"url":"...","headers":{...}}
    """
    tenant_id = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=128)
    kind = models.CharField(max_length=16, help_text="email|webhook")
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_ops_alert_channel"
        indexes = [models.Index(fields=["tenant_id", "kind", "is_active"])]

    def __str__(self) -> str:
        """返回通道名称。"""
        return f"Channel<{self.id}:{self.name}>"


class OpsIncident(models.Model):
    """异常事件（可被合并/累计）。
    - key: 归一化键（基于 rule+group），用于合并同一对象的重复命中
    - payload: 最近一次命中的明细（可用于通知）
    - status: open|ack|closed
    - severity: low|medium|high
    - hit_count: 命中次数累计
    """
    tenant_id = models.CharField(max_length=64, db_index=True)
    rule = models.ForeignKey(OpsAlertRule, on_delete=models.CASCADE, related_name="incidents")
    key = models.CharField(max_length=256, db_index=True)
    severity = models.CharField(max_length=16, default="medium")
    status = models.CharField(max_length=16, default="open")
    payload = models.JSONField(default=dict, blank=True)
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    hit_count = models.IntegerField(default=1)

    class Meta:
        db_table = "ai_ops_incident"
        indexes = [models.Index(fields=["tenant_id", "status", "severity", "last_seen"]) , models.Index(fields=["tenant_id", "key"])]

    def __str__(self) -> str:
        """返回易读的事件键。"""
        return f"Incident<{self.id}:{self.key}>"