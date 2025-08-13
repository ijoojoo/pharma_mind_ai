# file: core/models/ai_billing.py
# purpose: 租户 Token 账户与流水，支持限额控制与扣费/充值记录
from __future__ import annotations
from django.db import models


class AiTenantTokenAccount(models.Model):
    tenant_id = models.CharField(max_length=64, db_index=True, unique=True)
    plan = models.CharField(max_length=64, default="basic")
    token_balance = models.BigIntegerField(default=0)
    soft_limit = models.BigIntegerField(default=0)
    hard_limit = models.BigIntegerField(default=0)
    status = models.CharField(max_length=16, default="active")  # active/suspended
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_tenant_token_account"


class AiTokenTransaction(models.Model):
    tenant_id = models.CharField(max_length=64, db_index=True)
    change = models.BigIntegerField()  # 正数=充值；负数=扣费
    reason = models.CharField(max_length=128, default="usage")  # usage/topup/adjust
    related_run_id = models.CharField(max_length=64, blank=True, default="")  # 关联 AiRun.trace_id
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_token_transaction"
        indexes = [models.Index(fields=["tenant_id", "created_at"])]