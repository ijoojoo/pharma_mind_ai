# file: core/views/ai/mock/bi.py
# purpose: Mock BI 数据：固定返回少量行 + 推荐图表；无需数据库
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json


_SAMPLE_ROWS = [
    {"biz_date": "2025-08-10", "amount": 1234.5},
    {"biz_date": "2025-08-11", "amount": 1567.8},
    {"biz_date": "2025-08-12", "amount": 1322.4},
]


class MockBiView(View):
    """POST /api/ai/mock/bi/ → 忽略 body，固定返回样例数据。"""

    def post(self, request: HttpRequest):
        try:
            _ = get_json(request)
            spec = {"type": "line", "x": "biz_date", "y": "amount"}
            return ok({"rows": _SAMPLE_ROWS, "count": len(_SAMPLE_ROWS), "chart_spec": spec})
        except Exception as e:
            return fail(str(e))

