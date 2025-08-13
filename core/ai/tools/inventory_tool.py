# file: core/ai/tools/inventory_tool.py
# purpose: 库存/补货通用计算工具（安全库存、再订货点等）
from __future__ import annotations
from math import sqrt

_Z_TABLE = {
    0.80: 0.8416,
    0.85: 1.0364,
    0.90: 1.2816,
    0.95: 1.6449,
    0.97: 1.8808,
    0.98: 2.0537,
    0.99: 2.3263,
}


def z_for_service_level(service_level: float) -> float:
    service_level = max(0.5, min(0.999, float(service_level or 0.95)))
    # 最近邻
    nearest = min(_Z_TABLE.keys(), key=lambda k: abs(k - service_level))
    return _Z_TABLE[nearest]


def calc_safety_stock(daily_demand_sigma: float, leadtime_days: float, *, service_level: float = 0.95) -> float:
    z = z_for_service_level(service_level)
    return max(0.0, z * float(daily_demand_sigma or 0.0) * sqrt(max(0.0, float(leadtime_days or 0.0))))


def calc_reorder_point(daily_demand_mean: float, leadtime_days: float, safety_stock: float) -> float:
    return max(0.0, float(daily_demand_mean or 0.0) * max(0.0, float(leadtime_days or 0.0)) + max(0.0, float(safety_stock or 0.0)))

