# file: core/ai/metrics.py
# purpose: AI 用量与性能指标：汇总 Token/CALL；按 provider/agent 维度统计；延迟分位数（P50/P90/P95/P99）
from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from django.db.models import Sum, Count, Avg
from core.models.ai_billing import AiTokenTransaction
from core.models.ai_logging import AiCallLog, AiRun


def _to_dt(v: Optional[str | datetime | date]) -> Optional[datetime]:
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime.combine(v, datetime.min.time())
    try:
        return datetime.fromisoformat(str(v))
    except Exception:
        return None


# ---- 基础汇总 ----

def usage_summary(tenant_id: str, start: Optional[str | datetime | date], end: Optional[str | datetime | date]) -> Dict[str, Any]:
    s = _to_dt(start)
    e = _to_dt(end)
    if not s and not e:
        # 默认统计近7天
        e = datetime.utcnow()
        s = e - timedelta(days=7)
    q_call = AiCallLog.objects.filter(run__tenant_id=tenant_id)
    q_tx = AiTokenTransaction.objects.filter(tenant_id=tenant_id)
    if s:
        q_call = q_call.filter(created_at__gte=s)
        q_tx = q_tx.filter(created_at__gte=s)
    if e:
        q_call = q_call.filter(created_at__lte=e)
        q_tx = q_tx.filter(created_at__lte=e)
    agg_call = q_call.aggregate(tokens_in=Sum("tokens_in"), tokens_out=Sum("tokens_out"), calls=Count("id"))
    agg_tx = q_tx.aggregate(tokens_delta=Sum("change"), txs=Count("id"))
    return {
        "tenant_id": tenant_id,
        "window": {"start": s, "end": e},
        "calls": int(agg_call["calls"] or 0),
        "tokens_in": int(agg_call["tokens_in"] or 0),
        "tokens_out": int(agg_call["tokens_out"] or 0),
        "tokens_delta": int(agg_tx["tokens_delta"] or 0),  # 负数为扣费，正数为充值
        "transactions": int(agg_tx["txs"] or 0),
    }


def recent_runs(tenant_id: str, limit: int = 20) -> list[dict]:
    rows = AiRun.objects.filter(tenant_id=tenant_id).order_by("-created_at")[:limit]
    return [
        {
            "trace_id": r.trace_id,
            "agent": r.agent,
            "latency_ms": r.latency_ms,
            "created_at": r.created_at,
        }
        for r in rows
    ]


# ---- 维度用量 ----

def usage_by_provider(tenant_id: str, start: Optional[str | datetime | date], end: Optional[str | datetime | date]) -> Dict[str, Any]:
    s = _to_dt(start)
    e = _to_dt(end)
    if not s and not e:
        e = datetime.utcnow()
        s = e - timedelta(days=7)
    base = AiCallLog.objects.filter(run__tenant_id=tenant_id)
    if s:
        base = base.filter(created_at__gte=s)
    if e:
        base = base.filter(created_at__lte=e)

    prov = (
        base.values("provider")
        .annotate(calls=Count("id"), tokens_in=Sum("tokens_in"), tokens_out=Sum("tokens_out"), latency_avg=Avg("latency_ms"))
        .order_by("provider")
    )
    prov_model = (
        base.values("provider", "model")
        .annotate(calls=Count("id"), tokens_in=Sum("tokens_in"), tokens_out=Sum("tokens_out"), latency_avg=Avg("latency_ms"))
        .order_by("provider", "model")
    )
    agent = (
        base.values("run__agent")
        .annotate(calls=Count("id"), tokens_in=Sum("tokens_in"), tokens_out=Sum("tokens_out"), latency_avg=Avg("latency_ms"))
        .order_by("run__agent")
    )

    def _cook(qs):
        return [
            {
                **({"provider": r.get("provider")} if "provider" in r else {}),
                **({"model": r.get("model")} if "model" in r else {}),
                **({"agent": r.get("run__agent")} if "run__agent" in r else {}),
                "calls": int(r.get("calls") or 0),
                "tokens_in": int(r.get("tokens_in") or 0),
                "tokens_out": int(r.get("tokens_out") or 0),
                "latency_avg": float(r.get("latency_avg") or 0.0),
            }
            for r in qs
        ]

    return {
        "tenant_id": tenant_id,
        "window": {"start": s, "end": e},
        "by_provider": _cook(prov),
        "by_provider_model": _cook(prov_model),
        "by_agent": _cook(agent),
    }


# ---- 延迟分位数 ----

def _percentiles(xs: List[int | float], ps=(50, 90, 95, 99)) -> Dict[str, float]:
    if not xs:
        return {f"p{p}": 0.0 for p in ps}
    arr = sorted(float(x) for x in xs if x is not None)
    n = len(arr)
    def _rank(p):
        # 最近位分位法（Nearest Rank）
        k = int(round(p / 100.0 * (n - 1)))
        k = max(0, min(n - 1, k))
        return arr[k]
    return {f"p{p}": round(_rank(p), 3) for p in ps}


def latency_percentiles(tenant_id: str, start: Optional[str | datetime | date], end: Optional[str | datetime | date], group: str = "provider") -> Dict[str, Any]:
    s = _to_dt(start)
    e = _to_dt(end)
    if not s and not e:
        e = datetime.utcnow()
        s = e - timedelta(days=7)
    base = AiCallLog.objects.filter(run__tenant_id=tenant_id)
    if s:
        base = base.filter(created_at__gte=s)
    if e:
        base = base.filter(created_at__lte=e)

    # overall
    all_lat = list(base.values_list("latency_ms", flat=True))
    overall = _percentiles([x or 0 for x in all_lat])

    groups: Dict[str, Dict[str, float]] = {}
    if group == "provider":
        keys = base.values_list("provider", flat=True).distinct()
        for k in keys:
            if k is None:
                continue
            lat = list(base.filter(provider=k).values_list("latency_ms", flat=True))
            groups[str(k)] = _percentiles([x or 0 for x in lat])
    elif group == "agent":
        keys = base.values_list("run__agent", flat=True).distinct()
        for k in keys:
            if k is None:
                continue
            lat = list(base.filter(run__agent=k).values_list("latency_ms", flat=True))
            groups[str(k)] = _percentiles([x or 0 for x in lat])
    elif group == "model":
        keys = base.values_list("model", flat=True).distinct()
        for k in keys:
            if k is None:
                continue
            lat = list(base.filter(model=k).values_list("latency_ms", flat=True))
            groups[str(k)] = _percentiles([x or 0 for x in lat])

    return {
        "tenant_id": tenant_id,
        "window": {"start": s, "end": e},
        "overall": overall,
        "by": group,
        "groups": groups,
    }