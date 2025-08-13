# file: core/ai/kpi/review.py
# purpose: KPI 复盘：对比实际 vs 目标，输出差额与进度状态
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional
from django.db.models import Sum
from core.models import Sale
from .targets import Period, _daterange


@dataclass
class ReviewResult:
    total_actual: float
    total_target: float
    gap: float
    gap_pct: float
    on_track: bool
    daily: List[Dict]


_DEF_TRACK_TOLERANCE = 0.05  # 允许 5% 偏差内视为达标


def _fetch_actuals(tenant_id: str, period: Period) -> Dict[date, float]:
    qs = (
        Sale.objects.filter(tenant_id=tenant_id, biz_date__gte=period.start, biz_date__lte=period.end)
        .values("biz_date")
        .annotate(amount=Sum("total_amount"))
        .order_by("biz_date")
    )
    data = {r["biz_date"]: float(r.get("amount") or 0.0) for r in qs}
    for d in _daterange(period.start, period.end):
        data.setdefault(d, 0.0)
    return dict(sorted(data.items(), key=lambda x: x[0]))


def review(*, tenant_id: str, period: Period, targets_daily: List[Dict], actuals_override: Optional[List[Dict]] = None, tolerance: float = _DEF_TRACK_TOLERANCE) -> ReviewResult:
    if actuals_override is None:
        actual_map = _fetch_actuals(tenant_id, period)
    else:
        actual_map = {}
        for r in actuals_override:
            d = r.get("date")
            if isinstance(d, str):
                d = datetime.fromisoformat(d).date()
            actual_map[d] = float(r.get("sales") or 0.0)
        # 对齐
        actual_map = {d: float(actual_map.get(d, 0.0)) for d in _daterange(period.start, period.end)}

    items: List[Dict] = []
    total_actual = 0.0
    total_target = 0.0
    for r in targets_daily:
        d = r["date"]
        if isinstance(d, str):
            d = datetime.fromisoformat(d).date()
        tgt = float(r.get("target") or 0.0)
        act = float(actual_map.get(d, 0.0))
        total_actual += act
        total_target += tgt
        diff = round(act - tgt, 2)
        status = "on_track" if (tgt <= 0 or diff / max(tgt, 1e-6) >= -tolerance) else "behind"
        items.append({"date": d, "target": round(tgt, 2), "actual": round(act, 2), "diff": diff, "status": status})

    gap = round(total_actual - total_target, 2)
    gap_pct = (gap / total_target * 100.0) if total_target > 0 else 0.0
    on_track = (gap_pct >= -tolerance * 100.0)

    return ReviewResult(
        total_actual=round(total_actual, 2),
        total_target=round(total_target, 2),
        gap=gap,
        gap_pct=round(gap_pct, 2),
        on_track=on_track,
        daily=items,
    )
