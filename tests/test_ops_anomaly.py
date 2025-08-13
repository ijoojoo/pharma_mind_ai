# file: tests/test_ops_anomaly.py
# purpose: OPS：异常检测核心逻辑（用 monkeypatch 替换真实 DB 读取）
from __future__ import annotations
from datetime import date, timedelta
from core.ai.ops import anomaly_rules as ar


def test_sales_drop_logic(monkeypatch):
    today = date.today()
    start = today - timedelta(days=7)

    def fake_fetch_sales_daily(tenant_id, start, end, group_by):
        # 最近 7 天均值为 100，最后一天为 20 → 降幅 80%
        rows = []
        for i in range(1, 8):
            d = today - timedelta(days=i)
            rows.append({"biz_date": d, "store_id": 1, "product_id": 2, "amount": 100.0})
        rows.append({"biz_date": today, "store_id": 1, "product_id": 2, "amount": 20.0})
        return rows

    monkeypatch.setattr(ar, "fetch_sales_daily", fake_fetch_sales_daily)
    rule = ar.Rule(id="r1", type="sales_drop", threshold_pct=30, lookback=7)
    res = ar.detect_sales_drop(tenant_id="t_demo", start=start, end=today, rule=rule)
    assert res and res[0]["drop_pct"] >= 30