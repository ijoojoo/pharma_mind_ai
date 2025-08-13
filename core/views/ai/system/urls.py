# file: core/views/ai/system/urls.py
# purpose: 系统路由整合（完整文件，新增 metrics/ready/live；保留先前所有端点）
from __future__ import annotations
from django.urls import path
from .billing import TokenBalanceView, TokenTopupView
from .model import ModelProviderListView, ModelPreferenceView, TenantDefaultModelView
from .usage import UsageSummaryView, RecentRunsView
from .health import AiHealthView, AiSelfcheckView
from .docs import AiOpenApiJsonView, AiDocsView, AiErrorCodesView
from .env import AiEnvView
from .metrics import AiMetricsView
from .ready_live import AiLiveView, AiReadyView

urlpatterns = [
    # 计费
    path("billing/balance/", TokenBalanceView.as_view(), name="ai_billing_balance"),
    path("billing/topup/", TokenTopupView.as_view(), name="ai_billing_topup"),

    # 模型
    path("model/providers/", ModelProviderListView.as_view(), name="ai_model_providers"),
    path("model/preference/", ModelPreferenceView.as_view(), name="ai_model_preference"),
    path("model/tenant_default/", TenantDefaultModelView.as_view(), name="ai_model_tenant_default"),

    # 用量
    path("usage/summary/", UsageSummaryView.as_view(), name="ai_usage_summary"),
    path("usage/runs/", RecentRunsView.as_view(), name="ai_usage_runs"),

    # 健康
    path("health/", AiHealthView.as_view(), name="ai_health"),
    path("selfcheck/", AiSelfcheckView.as_view(), name="ai_selfcheck"),

    # 文档 & 错误码
    path("openapi.json", AiOpenApiJsonView.as_view(), name="ai_openapi_json"),
    path("docs/", AiDocsView.as_view(), name="ai_docs"),
    path("errors/", AiErrorCodesView.as_view(), name="ai_errors"),

    # 环境探针
    path("env/", AiEnvView.as_view(), name="ai_env"),

    # 运维探针
    path("metrics/", AiMetricsView.as_view(), name="ai_metrics"),
    path("live/", AiLiveView.as_view(), name="ai_live"),
    path("ready/", AiReadyView.as_view(), name="ai_ready"),
]
