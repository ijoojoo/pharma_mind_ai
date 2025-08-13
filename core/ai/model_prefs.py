# file: core/ai/model_prefs.py
# purpose: 模型偏好存取与解析（用户 > 租户 > 环境 > 回退）；为 Orchestrator 提供 get_effective_model()
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from django.db import transaction

from core.ai.llm.registry import (
    normalize_provider_key,
    has_provider,
    get_provider_meta,
    list_providers as _list_providers,
)
from core.models.ai_settings import (
    AiTenantDefaultModel,
    AiModelPreference,
)


class InvalidProvider(Exception):
    pass


@dataclass
class EffectiveModel:
    provider: str
    model_name: Optional[str]
    source: str  # 'user' | 'tenant' | 'env' | 'fallback'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------
# CRUD APIs
# ---------------------------

@transaction.atomic
def set_user_model(*, tenant_id: str, user_id: str, provider: str, model_name: Optional[str] = None, is_active: bool = True) -> Dict[str, Any]:
    key = normalize_provider_key(provider)
    if not key or not has_provider(key):
        raise InvalidProvider(f"Unknown provider: {provider}")
    obj, created = AiModelPreference.objects.update_or_create(
        tenant_id=tenant_id,
        user_id=user_id,
        defaults={
            "provider_key": key,
            "model_name": model_name or "",
            "is_active": is_active,
        },
    )
    return {
        "tenant_id": obj.tenant_id,
        "user_id": obj.user_id,
        "provider": obj.provider_key,
        "model_name": obj.model_name or None,
        "is_active": obj.is_active,
        "created": created,
    }


def get_user_model(*, tenant_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    obj = AiModelPreference.objects.filter(tenant_id=tenant_id, user_id=user_id).first()
    if not obj:
        return None
    return {
        "tenant_id": obj.tenant_id,
        "user_id": obj.user_id,
        "provider": obj.provider_key,
        "model_name": obj.model_name or None,
        "is_active": obj.is_active,
    }


@transaction.atomic
def set_tenant_default_model(*, tenant_id: str, provider: str, model_name: Optional[str] = None, is_active: bool = True) -> Dict[str, Any]:
    key = normalize_provider_key(provider)
    if not key or not has_provider(key):
        raise InvalidProvider(f"Unknown provider: {provider}")
    obj, _ = AiTenantDefaultModel.objects.update_or_create(
        tenant_id=tenant_id,
        defaults={
            "provider_key": key,
            "model_name": model_name or "",
            "is_active": is_active,
        },
    )
    return {
        "tenant_id": obj.tenant_id,
        "provider": obj.provider_key,
        "model_name": obj.model_name or None,
        "is_active": obj.is_active,
    }


def get_tenant_default_model(*, tenant_id: str) -> Optional[Dict[str, Any]]:
    obj = AiTenantDefaultModel.objects.filter(tenant_id=tenant_id).first()
    if not obj:
        return None
    return {
        "tenant_id": obj.tenant_id,
        "provider": obj.provider_key,
        "model_name": obj.model_name or None,
        "is_active": obj.is_active,
    }


# ---------------------------
# Resolution
# ---------------------------

def get_effective_model(*, tenant_id: str, user_id: Optional[str] = None, env_provider: Optional[str] = None, fallback_provider: str = "mock") -> EffectiveModel:
    """解析有效模型（用户 > 租户 > 环境 > 回退）。
    - env_provider: 可来自 settings/环境变量（如 LLM_PROVIDER），可为空。
    - fallback_provider: 最终回退（默认 mock）。
    返回 EffectiveModel(provider, model_name, source)
    """
    # 1) 用户级偏好
    if user_id:
        up = AiModelPreference.objects.filter(tenant_id=tenant_id, user_id=user_id, is_active=True).first()
        if up and has_provider(up.provider_key):
            model = up.model_name or get_provider_meta(up.provider_key).default_model
            return EffectiveModel(provider=up.provider_key, model_name=model, source="user")

    # 2) 租户默认
    tp = AiTenantDefaultModel.objects.filter(tenant_id=tenant_id, is_active=True).first()
    if tp and has_provider(tp.provider_key):
        model = tp.model_name or get_provider_meta(tp.provider_key).default_model
        return EffectiveModel(provider=tp.provider_key, model_name=model, source="tenant")

    # 3) 环境默认
    key = normalize_provider_key(env_provider) if env_provider else None
    if key and has_provider(key):
        model = get_provider_meta(key).default_model
        return EffectiveModel(provider=key, model_name=model, source="env")

    # 4) 最终回退
    fb = normalize_provider_key(fallback_provider) or "mock"
    meta = get_provider_meta(fb)
    return EffectiveModel(provider=meta.key, model_name=meta.default_model, source="fallback")


def list_supported_providers() -> list[dict]:
    return _list_providers()


__all__ = [
    "InvalidProvider",
    "EffectiveModel",
    "set_user_model",
    "get_user_model",
    "set_tenant_default_model",
    "get_tenant_default_model",
    "get_effective_model",
    "list_supported_providers",
]
