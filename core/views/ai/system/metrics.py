# file: core/views/ai/system/metrics.py
# purpose: Prometheus 指标导出端点（明文），默认启用；可通过 settings.AI_METRICS_ENABLED 控制
from __future__ import annotations
from django.views import View
from django.http import HttpResponse
from django.conf import settings
from core.observability.metrics import REGISTRY


class AiMetricsView(View):
    """GET /api/ai/system/metrics/ → Prometheus 文本格式。"""

    def get(self, _):
        if not bool(getattr(settings, "AI_METRICS_ENABLED", True)):
            return HttpResponse("metrics disabled\n", content_type="text/plain; charset=utf-8", status=404)
        text = REGISTRY.export_prometheus()
        return HttpResponse(text, content_type="text/plain; version=0.0.4; charset=utf-8")

