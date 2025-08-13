# file: core/models/ai_settings.py
# purpose: 用户与租户的全局模型偏好设置（Provider/型号），用于按租户/用户生效
from __future__ import annotations
from django.db import models

PROVIDERS = (
    ("gpt5", "GPT-5"),
    ("gemini", "Gemini"),
    ("deepseek", "DeepSeek"),
    ("zhipu", "Zhipu"),
    ("mock", "Mock"),
)


class AiTenantDefaultModel(models.Model):
    tenant_id = models.CharField(max_length=64, db_index=True, unique=True)
    provider_key = models.CharField(max_length=32, choices=PROVIDERS)
    model_name = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_tenant_default_model"


class AiModelPreference(models.Model):
    tenant_id = models.CharField(max_length=64, db_index=True)
    user_id = models.CharField(max_length=64, db_index=True)
    provider_key = models.CharField(max_length=32, choices=PROVIDERS)
    model_name = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_model_preference"
        unique_together = ("tenant_id", "user_id")
        indexes = [models.Index(fields=["tenant_id", "user_id"])]