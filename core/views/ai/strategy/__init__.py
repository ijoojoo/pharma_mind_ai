# file: core/ai/strategy/__init__.py
# purpose: Strategy 包统一出口（已彻底移除旧命名 promotion/replenishment 的别名与再导出）
from __future__ import annotations

# 导出标准命名：定价/促销/补货
from .price import suggest_prices, PriceBound  # 定价：建议价与价格带
from .promo import suggest_promotions          # 促销：候选与折扣建议
from .replenish import suggest_replenishment  # 补货：安全库存/再订货点/建议订货量

__all__ = [
    "suggest_prices",
    "PriceBound",
    "suggest_promotions",
    "suggest_replenishment",
]
