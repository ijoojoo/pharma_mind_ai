# file: tests/test_kpi.py
# purpose: KPI：目标拟定与复盘
from __future__ import annotations
from datetime import date, timedelta
from core.ai.kpi.targets import Period, make_targets
from core.ai.kpi.review import review


def test_kpi_make_and_review():
    period = Period(start=date.today(), end=date.today() + timedelta(days=6))
    plan = make_targets(tenant_id="t_demo", period=period, goal_lift_pct=10.0, baseline_override=[{"date": str(period.start + timedelta(days=i)), "sales": 100.0} for i in range(7)])
    assert plan["total_target"] > plan["total_baseline"]

    rr = review(tenant_id="t_demo", period=period, targets_daily=plan["daily"], actuals_override=[{"date": str(period.start + timedelta(days=i)), "sales": 110.0} for i in range(7)])
    assert rr.on_track is True

