# file: core/views/ai/strategy/urls.py
# purpose: Strategy 路由聚合（仅保留新命名：/price/ /promo/ /replenish/；已移除 /promotion/ 与 /replenishment/ 兼容路由）
from __future__ import annotations
from django.urls import path
from .price import StrategyPriceView
from .promo import StrategyPromoView
from .replenish import StrategyReplenishView

urlpatterns = [
    path("price/", StrategyPriceView.as_view(), name="ai_strategy_price"),
    path("promo/", StrategyPromoView.as_view(), name="ai_strategy_promo"),
    path("replenish/", StrategyReplenishView.as_view(), name="ai_strategy_replenish"),
]