# file: core/views/ai/system/urls.py
# purpose: 扩展系统路由：加入用量/最近调用/维度统计/延迟分位数
from __future__ import annotations
from django.urls import path
from .billing import TokenBalanceView, TokenTopupView
from .model import ModelProviderListView, ModelPreferenceView, TenantDefaultModelView
from .usage import UsageSummaryView, RecentRunsView, ProviderUsageView, LatencyStatsView


urlpatterns = [
    path("billing/balance/", TokenBalanceView.as_view(), name="ai_billing_balance"),
    path("billing/topup/", TokenTopupView.as_view(), name="ai_billing_topup"),

    path("model/providers/", ModelProviderListView.as_view(), name="ai_model_providers"),
    path("model/preference/", ModelPreferenceView.as_view(), name="ai_model_preference"),
    path("model/tenant_default/", TenantDefaultModelView.as_view(), name="ai_model_tenant_default"),

    path("usage/summary/", UsageSummaryView.as_view(), name="ai_usage_summary"),
    path("usage/runs/", RecentRunsView.as_view(), name="ai_usage_runs"),
    path("usage/provider/", ProviderUsageView.as_view(), name="ai_usage_by_provider"),
    path("usage/latency/", LatencyStatsView.as_view(), name="ai_usage_latency"),
]