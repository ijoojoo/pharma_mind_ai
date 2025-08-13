# file: core/views/ai/mock/urls.py
# purpose: Mock 路由聚合：/api/ai/mock/ 下的子路由
from __future__ import annotations
from django.urls import path
from .chat import MockChatView
from .bi import MockBiView
from .ops import MockOpsView
from .strategy import MockStrategyPriceView, MockStrategyPromoView, MockStrategyReplenishView

urlpatterns = [
    path("chat/", MockChatView.as_view(), name="ai_mock_chat"),
    path("bi/", MockBiView.as_view(), name="ai_mock_bi"),
    path("ops/", MockOpsView.as_view(), name="ai_mock_ops"),
    path("strategy/price/", MockStrategyPriceView.as_view(), name="ai_mock_strategy_price"),
    path("strategy/promo/", MockStrategyPromoView.as_view(), name="ai_mock_strategy_promo"),
    path("strategy/replenish/", MockStrategyReplenishView.as_view(), name="ai_mock_strategy_replenish"),
]