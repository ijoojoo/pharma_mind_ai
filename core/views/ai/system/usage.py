# file: core/views/ai/system/usage.py
# purpose: 账单与用量接口：时间窗汇总 + 最近调用列表 + 按 provider/agent 统计 + 延迟分位数
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail
from core.ai.metrics import usage_summary, recent_runs, usage_by_provider, latency_percentiles


class UsageSummaryView(View):
    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            start = request.GET.get("from")
            end = request.GET.get("to")
            data = usage_summary(tenant_id, start, end)
            return ok(data)
        except Exception as e:
            return fail(str(e))


class RecentRunsView(View):
    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            limit = int(request.GET.get("limit", 20))
            data = recent_runs(tenant_id, limit=limit)
            return ok({"items": data})
        except Exception as e:
            return fail(str(e))


class ProviderUsageView(View):
    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            start = request.GET.get("from")
            end = request.GET.get("to")
            data = usage_by_provider(tenant_id, start, end)
            return ok(data)
        except Exception as e:
            return fail(str(e))


class LatencyStatsView(View):
    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            start = request.GET.get("from")
            end = request.GET.get("to")
            by = request.GET.get("by", "provider")  # provider|agent|model
            data = latency_percentiles(tenant_id, start, end, group=by)
            return ok(data)
        except Exception as e:
            return fail(str(e))