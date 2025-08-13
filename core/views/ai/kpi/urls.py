# file: core/views/ai/kpi/urls.py
# purpose: KPI 路由聚合：target_plan / review
from __future__ import annotations
from django.urls import path
from .target_plan import KpiTargetPlanView
from .review import KpiReviewView

urlpatterns = [
    path("target_plan/", KpiTargetPlanView.as_view(), name="ai_kpi_target_plan"),
    path("review/", KpiReviewView.as_view(), name="ai_kpi_review"),
]
