# file: core/ai/kpi/targets.py
# purpose: KPI 目标拟定：基于历史（同比/上一周期）与目标增幅，生成总目标与按日拆分
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.db.models import Sum
from core.models import Sale  # 需包含字段：tenant_id, biz_date(date), total_amount(numeric)


@dataclass
class Period:
    start: date
    end: date

    @classmethod
    def from_payload(cls, p: Dict) -> "Period":
        s = p.get("start")
        e = p.get("end")
        if not s or not e:
            raise ValueError("period.start/end required (YYYY-MM-DD)")
        if isinstance(s, str):
            s = datetime.fromisoformat(s).date()
        if isinstance(e, str):
            e = datetime.fromisoformat(e).date()
        if e < s:
            raise ValueError("period.end must be >= period.start")
        return cls(start=s, end=e)

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


# -------- baseline fetch --------

def _daterange(d0: date, d1: date) -> List[date]:
    n = (d1 - d0).days
    return [d0 + timedelta(days=i) for i in range(n + 1)]


def _fetch_sales_daily(tenant_id: str, period: Period) -> Dict[date, float]:
    qs = (
        Sale.objects.filter(tenant_id=tenant_id, biz_date__gte=period.start, biz_date__lte=period.end)
        .values("biz_date")
        .annotate(amount=Sum("total_amount"))
        .order_by("biz_date")
    )
    data = {r["biz_date"]: float(r.get("amount") or 0.0) for r in qs}
    # 填补缺失日期
    for d in _daterange(period.start, period.end):
        data.setdefault(d, 0.0)
    return dict(sorted(data.items(), key=lambda x: x[0]))


def _shift_period(period: Period, *, days: int) -> Period:
    return Period(start=period.start - timedelta(days=days), end=period.end - timedelta(days=days))


def _yoy_period(period: Period) -> Period:
    return Period(start=period.start.replace(year=period.start.year - 1), end=period.end.replace(year=period.end.year - 1))


def fetch_baseline(tenant_id: str, period: Period, *, mode: str = "last_period") -> Dict[date, float]:
    """mode: last_period | yoy
    - last_period: 取紧邻上一段等长区间
    - yoy: 取去年同期
    """
    if mode == "yoy":
        p = _yoy_period(period)
    else:
        p = _shift_period(period, days=period.days)
    return _fetch_sales_daily(tenant_id, p)


# -------- target plan --------

def make_targets(*, tenant_id: str, period: Period, goal_lift_pct: float = 10.0, baseline_mode: str = "last_period", baseline_override: Optional[List[Dict]] = None) -> Dict:
    """
    返回：{
      total_baseline, total_target, daily: [{date, baseline, target}], lift_pct
    }
    baseline_override: 可传入自定义历史 [{date: 'YYYY-MM-DD', sales: number}]（优先于从库读取）
    """
    if baseline_override is not None:
        # 使用外部传入的 baseline
        base_map: Dict[date, float] = {}
        for r in baseline_override:
            d = r.get("date")
            if isinstance(d, str):
                d = datetime.fromisoformat(d).date()
            base_map[d] = float(r.get("sales") or 0.0)
        # 对齐目标周期
        base = {d: float(base_map.get(d, 0.0)) for d in _daterange(period.start, period.end)}
    else:
        base = fetch_baseline(tenant_id, period, mode=baseline_mode)
        # 若结果与目标期天数不一致，按日期对齐填零
        base = {d: float(base.get(d, 0.0)) for d in _daterange(period.start, period.end)}

    total_base = sum(base.values())
    lift = max(-90.0, float(goal_lift_pct))  # 限制下限，避免负到不合理
    total_target = round(total_base * (1.0 + lift / 100.0), 2)

    # 按比例分摊到日
    daily: List[Dict] = []
    denom = total_base if total_base > 0 else period.days
    for d in _daterange(period.start, period.end):
        weight = (base[d] / denom) if total_base > 0 else (1.0 / period.days)
        tgt = round(total_target * weight, 2)
        daily.append({"date": d, "baseline": round(base[d], 2), "target": tgt})

    return {
        "period": {"start": period.start, "end": period.end, "days": period.days},
        "lift_pct": lift,
        "total_baseline": round(total_base, 2),
        "total_target": total_target,
        "daily": daily,
        "baseline_mode": baseline_mode,
    }

