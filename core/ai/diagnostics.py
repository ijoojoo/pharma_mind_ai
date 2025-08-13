# file: core/ai/diagnostics.py
# purpose: AI 模块运行健康检查/自检工具（数据库/缓存/计费/模型配置）。
# - 仅做“无副作用”的环境与配置验证，不对外部服务发真实请求（避免超时/成本）。
# - 提供 run_health()（基础可用性）与 run_selfcheck(tenant_id)（结合租户上下文）。
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.utils import OperationalError

from core.ai.llm.registry import normalize_provider_key, has_provider, get_provider_meta
from core.models.ai_billing import AiTenantTokenAccount


@dataclass
class Check:
    """单项检查结果（通过/失败 + 详情）。"""
    name: str
    ok: bool
    detail: str | None = None
    data: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthReport:
    """健康报告聚合结果。"""
    ok: bool
    items: list[Check]

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "items": [c.to_dict() for c in self.items]}


# --------- 低级检查 ---------

def check_database() -> Check:
    """检查数据库可连接与基本 SELECT 权限。"""
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
        return Check("database", ok=(row and row[0] == 1), detail=None)
    except OperationalError as e:
        return Check("database", ok=False, detail=str(e))
    except Exception as e:  # pragma: no cover
        return Check("database", ok=False, detail=str(e))


def check_cache() -> Check:
    """检查缓存服务可用性（set/get）。"""
    try:
        k = "ai:health:probe"
        cache.set(k, "1", timeout=10)
        v = cache.get(k)
        return Check("cache", ok=(v == "1"))
    except Exception as e:
        return Check("cache", ok=False, detail=str(e))


def check_settings() -> Check:
    """检查关键 settings 是否存在（非强制，但便于提示）。"""
    miss: list[str] = []
    for key in ["AI_RATE_LIMIT", "AI_LOG_RETENTION_DAYS"]:
        _ = getattr(settings, key, None)
        if _ is None:
            miss.append(key)
    ok = True  # 缺省也可运行
    detail = ("missing: " + ",".join(miss)) if miss else None
    return Check("settings", ok=ok, detail=detail, data={k: getattr(settings, k, None) for k in ["AI_RATE_LIMIT", "AI_LOG_RETENTION_DAYS"]})


# --------- 与 LLM/计费相关 ---------

def check_llm_provider(env_provider: Optional[str]) -> Check:
    """检查环境默认的 LLM 提供商配置是否合理（不发起外部请求）。"""
    key = normalize_provider_key(env_provider) if env_provider else None
    if key and not has_provider(key):
        return Check("llm_provider", ok=False, detail=f"Unknown provider: {env_provider}")
    if not key:
        # 未设置走回退也允许，但给出提醒
        return Check("llm_provider", ok=True, detail="LLM_PROVIDER unset; fallback provider will be used")
    meta = get_provider_meta(key)
    # 针对已知 provider 做关键环境变量提示（以 gpt 为例）
    warns: list[str] = []
    if key == "gpt":
        if not getattr(settings, "OPENAI_API_KEY", None) and not getattr(settings, "OPENAI_API_KEY", ""):
            warns.append("OPENAI_API_KEY missing")
    return Check("llm_provider", ok=True, detail=("; ".join(warns) if warns else None), data={"provider": meta.key, "default_model": meta.default_model})


def check_billing_account(tenant_id: str) -> Check:
    """检查租户的计费账户是否存在。"""
    obj = AiTenantTokenAccount.objects.filter(tenant_id=tenant_id).first()
    if not obj:
        return Check("billing_account", ok=False, detail="AiTenantTokenAccount not found")
    detail = f"balance={int(obj.token_balance)} plan={obj.plan} status={obj.status}"
    return Check("billing_account", ok=True, detail=detail, data={"balance": int(obj.token_balance), "plan": obj.plan, "status": obj.status})


# --------- 聚合入口 ---------

def run_health() -> HealthReport:
    """基础健康（与租户无关）。"""
    env_provider = getattr(settings, "LLM_PROVIDER", None)
    items = [
        check_database(),
        check_cache(),
        check_settings(),
        check_llm_provider(env_provider),
    ]
    ok = all(it.ok for it in items)
    return HealthReport(ok=ok, items=items)


def run_selfcheck(*, tenant_id: str) -> HealthReport:
    """结合租户维度的自检（计费账户等）。"""
    base = run_health().items
    t_items = [check_billing_account(tenant_id)]
    items = base + t_items
    ok = all(it.ok for it in items)
    return HealthReport(ok=ok, items=items)
