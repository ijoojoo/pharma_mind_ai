# file: tests/test_strategy.py
# purpose: Strategy：定价/补货计算
from __future__ import annotations
from core.ai.strategy.pricing import suggest_price
from core.ai.strategy.replenishment import suggest_replenishment


def test_pricing_suggest():
    out = suggest_price({"cost": 10.0, "competitor_price": 20.0}, {"target_margin": 0.25, "comp_weight": 0.5})
    assert out["suggested_price"] > 10.0
    assert out["calc"]["base"] > 0


def test_replenishment_suggest():
    rows = suggest_replenishment(
        store_id="S1",
        items=[{"sku": "SKU1", "daily_demand_mean": 5, "daily_demand_sigma": 2, "leadtime_days": 3, "on_hand": 2, "on_order": 0, "service_level": 0.95, "pack_size": 6}],
        policy={"review_days": 7},
    )
    assert rows and rows[0]["suggest_order_qty"] >= 0
