# file: core/views/ai/urls.py
# purpose: 更新聚合路由，加入 kpi/（若你已手工添加，可忽略此段）
from __future__ import annotations
from django.urls import path, include

urlpatterns = [
    path("chat/", include("core.views.ai.chat.urls")),
    path("system/", include("core.views.ai.system.urls")),
    path("rag/", include("core.views.ai.rag.urls")),
    path("bi/", include("core.views.ai.bi.urls")),
    path("ops/", include("core.views.ai.ops.urls")),
    path("strategy/", include("core.views.ai.strategy.urls")),
    path("kpi/", include("core.views.ai.kpi.urls")),
    path("mock/", include("core.views.ai.mock.urls")),
]
