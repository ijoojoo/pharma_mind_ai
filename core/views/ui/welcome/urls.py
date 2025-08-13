# core/views/ui/welcome/urls.py
from django.urls import path
from .index import (
    kpi_today, sales_today_hourly, sales_seven_days,
    kpi_stores_progress, ai_dashboard_review,
)
urlpatterns = [
    path("kpi/today/", kpi_today),
    path("sales/today-hourly/", sales_today_hourly),
    path("sales/seven-days/", sales_seven_days),
    path("kpi/stores-progress/", kpi_stores_progress),
    path("dashboard/review/", ai_dashboard_review),
]
