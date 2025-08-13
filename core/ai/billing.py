# file: core/ai/billing.py
# purpose: 计费与余额控制（软/硬阈值预警；授权-结算两段式；入账流水）
#          向后兼容旧接口：InsufficientTokens、ensure_can_consume、deduct_tokens、get_or_create_account、topup_tokens
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from contextlib import contextmanager
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.conf import settings
import logging

from core.models.ai_billing import AiTenantTokenAccount, AiTokenTransaction

logger = logging.getLogger(__name__)


# ---- Exceptions -------------------------------------------------------------
class AccountSuspended(Exception):
    """账号被禁用/冻结。"""
    pass


class InsufficientBalance(Exception):
    """余额不足（硬阈值以下）。"""
    pass


class InsufficientTokens(InsufficientBalance):
    """向后兼容旧名称：等价于 InsufficientBalance。"""
    pass


# ---- DTO -------------------------------------------------------------------
@dataclass
class AuthorizationResult:
    allowed: bool
    reason: str
    tenant_id: str
    estimate_tokens: int
    snapshot: Dict[str, Any]

    def to_dict(self):
        return asdict(self)


# ---- Internals --------------------------------------------------------------
@contextmanager
def _account_lock(tenant_id: str):
    with transaction.atomic():
        acct = AiTenantTokenAccount.objects.select_for_update().filter(tenant_id=tenant_id).first()
        if not acct:
            # 为兼容历史逻辑，这里不自动创建，抛出不足错误
            raise InsufficientBalance("Token account not found for tenant")
        yield acct


def _now():
    return timezone.now()


def _int_tokens(v) -> int:
    try:
        return int(round(float(v or 0)))
    except Exception:
        return 0


# ---- Account helpers --------------------------------------------------------

def get_or_create_account(*, tenant_id: str, defaults: Optional[Dict[str, Any]] = None) -> AiTenantTokenAccount:
    """获取或创建租户账户。若不存在则以安全默认值创建。"""
    defaults = defaults or {}
    obj, _ = AiTenantTokenAccount.objects.get_or_create(
        tenant_id=tenant_id,
        defaults={
            "plan": defaults.get("plan", "free"),
            "token_balance": defaults.get("token_balance", 0),
            "soft_limit": defaults.get("soft_limit", 100),
            "hard_limit": defaults.get("hard_limit", 0),
            "status": defaults.get("status", "active"),
        },
    )
    return obj


def get_balance(*, tenant_id: str) -> Dict[str, Any]:
    acct = get_or_create_account(tenant_id=tenant_id)
    return {
        "tenant_id": acct.tenant_id,
        "plan": getattr(acct, "plan", None),
        "token_balance": int(getattr(acct, "token_balance", 0) or 0),
        "soft_limit": int(getattr(acct, "soft_limit", 0) or 0),
        "hard_limit": int(getattr(acct, "hard_limit", 0) or 0),
        "status": getattr(acct, "status", "active"),
        "updated_at": getattr(acct, "updated_at", None),
    }


# ---- Authorization & Settlement --------------------------------------------

def begin_authorize(*, tenant_id: str, estimate_tokens: int, reason: str = "llm_estimate") -> AuthorizationResult:
    """预授权：校验余额是否可覆盖预计 tokens；低于 soft_limit 仅预警，不阻断。"""
    est = _int_tokens(estimate_tokens)
    with _account_lock(tenant_id) as acct:
        if getattr(acct, "status", "active") != "active":
            raise AccountSuspended("Account is not active")
        post = int(acct.token_balance) - est
        hard = int(getattr(acct, "hard_limit", 0) or 0)
        soft = int(getattr(acct, "soft_limit", 0) or 0)
        if post < hard:
            return AuthorizationResult(
                allowed=False,
                reason=f"balance would drop below hard_limit: {post} < {hard}",
                tenant_id=tenant_id,
                estimate_tokens=est,
                snapshot={
                    "token_balance": int(acct.token_balance),
                    "soft_limit": soft,
                    "hard_limit": hard,
                },
            )
        # 仅发预警，不扣费
        if post < soft:
            try:
                maybe_alert_low_balance(tenant_id=tenant_id, balance=post, soft_limit=soft)
            except Exception:
                logger.warning("low balance alert failed", exc_info=True)
        return AuthorizationResult(
            allowed=True,
            reason="ok",
            tenant_id=tenant_id,
            estimate_tokens=est,
            snapshot={
                "token_balance": int(acct.token_balance),
                "soft_limit": soft,
                "hard_limit": hard,
            },
        )


def ensure_can_consume(*, tenant_id: str, estimate_tokens: int, reason: str = "llm_estimate") -> Dict[str, Any]:
    """旧代码兼容：快速余额校验（不扣费）。不足则抛 InsufficientTokens。"""
    res = begin_authorize(tenant_id=tenant_id, estimate_tokens=estimate_tokens, reason=reason)
    if not res.allowed:
        raise InsufficientTokens(res.reason)
    return res.to_dict()


def finalize_or_rollback(*, tenant_id: str, run_id: Optional[str], actual_tokens: int, success: bool, reason: str = "llm_usage") -> Dict[str, Any]:
    """结算：成功则按实际 tokens 扣费并记流水；失败则跳过（可扩展最小扣费策略）。"""
    used = _int_tokens(actual_tokens)
    if not success or used <= 0:
        return {"deducted": 0, "skipped": True}
    with _account_lock(tenant_id) as acct:
        hard = int(getattr(acct, "hard_limit", 0) or 0)
        post = int(acct.token_balance) - used
        if post < hard:
            raise InsufficientBalance(f"finalize would drop below hard_limit: {post} < {hard}")
        # 扣减余额
        AiTenantTokenAccount.objects.filter(id=acct.id).update(token_balance=F("token_balance") - used, updated_at=_now())
        # 记录流水
        tx = AiTokenTransaction.objects.create(
            tenant_id=tenant_id,
            change=-used,
            reason=reason,
            related_run_id=run_id or "",
        )
        # 预警（扣费后）
        acct.refresh_from_db(fields=["token_balance", "soft_limit"])  # type: ignore
        soft = int(getattr(acct, "soft_limit", 0) or 0)
        if int(acct.token_balance) < soft:
            try:
                maybe_alert_low_balance(tenant_id=tenant_id, balance=int(acct.token_balance), soft_limit=soft)
            except Exception:
                logger.warning("low balance alert failed", exc_info=True)
        return {"deducted": used, "transaction_id": tx.id, "balance": int(acct.token_balance)}


def deduct_tokens(*, tenant_id: str, tokens: int, reason: str = "llm_usage", run_id: Optional[str] = None) -> Dict[str, Any]:
    """旧代码兼容：直接扣费别名，内部使用 finalize_or_rollback(success=True)。"""
    return finalize_or_rollback(tenant_id=tenant_id, run_id=run_id, actual_tokens=tokens, success=True, reason=reason)


# ---- Topup & Alerts ---------------------------------------------------------

def topup(*, tenant_id: str, tokens: int, reason: str = "manual_topup") -> Dict[str, Any]:
    add = _int_tokens(tokens)
    if add <= 0:
        return {"added": 0}
    acct = get_or_create_account(tenant_id=tenant_id)
    with transaction.atomic():
        AiTenantTokenAccount.objects.filter(id=acct.id).update(token_balance=F("token_balance") + add, updated_at=_now())
        tx = AiTokenTransaction.objects.create(tenant_id=tenant_id, change=add, reason=reason, related_run_id="")
    acct.refresh_from_db(fields=["token_balance"])  # type: ignore
    return {"added": add, "transaction_id": tx.id, "balance": int(acct.token_balance)}


def topup_tokens(*, tenant_id: str, tokens: int, reason: str = "manual_topup") -> Dict[str, Any]:
    """旧接口别名：等价于 topup()。"""
    return topup(tenant_id=tenant_id, tokens=tokens, reason=reason)


def maybe_alert_low_balance(*, tenant_id: str, balance: int, soft_limit: int) -> None:
    """低余额预警：优先走信号或邮件；未配置则写日志。
    settings 中可配置：AI_BILLING_NOTIFY_EMAILS = {tenant_id: ["ops@example.com"]}
    """
    emails = {}
    try:
        emails = getattr(settings, "AI_BILLING_NOTIFY_EMAILS", {}) or {}
    except Exception:
        emails = {}
    recipients = emails.get(tenant_id) or emails.get("*") or []
    msg = f"[AI Billing] Tenant {tenant_id} low balance: {balance} < soft_limit {soft_limit}"
    if recipients:
        try:
            from django.core.mail import send_mail
            send_mail(
                subject="AI 余额预警",
                message=msg,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=recipients,
                fail_silently=True,
            )
        except Exception:
            logger.warning("send low balance email failed", exc_info=True)
    logger.warning(msg)


__all__ = [
    "AccountSuspended",
    "InsufficientBalance",
    "InsufficientTokens",
    "AuthorizationResult",
    "get_or_create_account",
    "get_balance",
    "begin_authorize",
    "ensure_can_consume",
    "finalize_or_rollback",
    "deduct_tokens",
    "topup",
    "topup_tokens",
    "maybe_alert_low_balance",
]