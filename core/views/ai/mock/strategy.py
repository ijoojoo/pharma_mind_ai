# file: core/views/ai/mock/strategy.py
# purpose: Mock Strategy：定价/促销/补货的演示数据
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json


class MockStrategyPriceView(View):
    """POST /api/ai/mock/strategy/price/ → 固定两条建议价。"""

    def post(self, request: HttpRequest):
        try:
            _ = get_json(request)
            items = [
                {"product_id": 101, "current_price": 19.9, "suggested_price": 21.0, "reason": "按目标毛利 30%"},
                {"product_id": 102, "current_price": 9.9, "suggested_price": 9.4,  "reason": "销量偏低，下调 5%"},
            ]
            return ok({"items": items})
        except Exception as e:
            return fail(str(e))


class MockStrategyPromoView(View):
    """POST /api/ai/mock/strategy/promo/ → 固定返回两条促销候选。"""

    def post(self, request: HttpRequest):
        try:
            _ = get_json(request)
            items = [
                {"product_id": 101, "drop_pct": 38.5, "inventory": 120, "suggest_discount": 0.15},
                {"product_id": 102, "drop_pct": 62.0, "inventory": 80,  "suggest_discount": 0.20},
            ]
            return ok({"items": items, "count": len(items)})
        except Exception as e:
            return fail(str(e))


class MockStrategyReplenishView(View):
    """POST /api/ai/mock/strategy/replenish/ → 固定返回三条补货建议。"""

    def post(self, request: HttpRequest):
        try:
            _ = get_json(request)
            items = [
                {"product_id": 101, "daily_mean": 12.3, "daily_sigma": 3.1, "safety_stock": 8.1,  "reorder_point": 94.2, "on_hand": 60, "suggest_qty": 34},
                {"product_id": 102, "daily_mean": 4.5,  "daily_sigma": 1.8, "safety_stock": 4.7,  "reorder_point": 36.2, "on_hand": 50, "suggest_qty": 0},
                {"product_id": 103, "daily_mean": 20.0, "daily_sigma": 6.0, "safety_stock": 15.8, "reorder_point": 155.8,"on_hand": 100,"suggest_qty": 56},
            ]
            return ok({"items": items, "count": len(items)})
        except Exception as e:
            return fail(str(e))

