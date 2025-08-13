# file: core/views/ai/ops/urls.py
# purpose: OPS 路由（在原有基础上追加规则/通道/事件/扫描接口；保持兼容）
from django.urls import path
from .daily_insight import OpsDailyInsightView
from .anomaly import OpsAnomalyView
from .rules import OpsRuleListCreateView, OpsRuleDetailView
from .channels import OpsChannelListCreateView, OpsChannelDetailView
from .incidents import OpsIncidentListView, OpsIncidentActionView
from .scan import OpsScanView

urlpatterns = [
    # 兼容保留
    path("daily_insight/", OpsDailyInsightView.as_view(), name="ai_ops_daily_insight"),
    path("anomaly/", OpsAnomalyView.as_view(), name="ai_ops_anomaly"),
    # 新增：规则/通道/事件/扫描
    path("rules/", OpsRuleListCreateView.as_view(), name="ai_ops_rules"),
    path("rules/<str:rid>/", OpsRuleDetailView.as_view(), name="ai_ops_rule_detail"),
    path("channels/", OpsChannelListCreateView.as_view(), name="ai_ops_channels"),
    path("channels/<str:cid>/", OpsChannelDetailView.as_view(), name="ai_ops_channel_detail"),
    path("channels/<str:cid>/<str:action>/", OpsChannelDetailView.as_view(), name="ai_ops_channel_action"),
    path("incidents/", OpsIncidentListView.as_view(), name="ai_ops_incidents"),
    path("incidents/<str:iid>/<str:action>/", OpsIncidentActionView.as_view(), name="ai_ops_incident_action"),
    path("scan/", OpsScanView.as_view(), name="ai_ops_scan"),
]
