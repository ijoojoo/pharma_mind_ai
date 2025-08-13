# file: core/views/ai/ops/urls.py
# purpose: OPS 路由（保持与之前一致，无需变更；此处补充以便一次性落盘）
from django.urls import path
from .daily_insight import OpsDailyInsightView
from .anomaly import OpsAnomalyView

urlpatterns = [
    path("daily_insight/", OpsDailyInsightView.as_view(), name="ai_ops_daily_insight"),
    path("anomaly/", OpsAnomalyView.as_view(), name="ai_ops_anomaly"),
]
