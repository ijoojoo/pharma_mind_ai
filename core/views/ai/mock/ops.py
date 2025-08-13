# file: core/views/ai/mock/ops.py
# purpose: Mock OPS：返回示例异常命中
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json


class MockOpsView(View):
    """POST /api/ai/mock/ops/ → 固定返回 2 条异常，用于列表与状态切换 UI。"""

    def post(self, request: HttpRequest):
        try:
            _ = get_json(request)
            items = [
                {"type": "sales_drop", "group": {"store_id": 1, "product_id": 101}, "drop_pct": 42.3, "severity": "high"},
                {"type": "stockout", "group": {"store_id": 2, "product_id": 102}, "qty": 0, "severity": "high"},
            ]
            return ok({"items": items, "count": len(items)})
        except Exception as e:
            return fail(str(e))
