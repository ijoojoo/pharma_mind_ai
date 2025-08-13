# file: core/views/ai/bi/exec.py
# purpose: 执行只读 SQL 并返回 rows + chart_spec；支持分页、缓存；可选 LLM 解读
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.tools.sql_tool import run_readonly, run_readonly_paginated, cached_run_readonly
from core.ai.bi.chart_spec import suggest_spec
from core.ai.orchestrator import Orchestrator


class BiSqlExecView(View):
    """直接执行经过白名单校验的 SELECT 语句（慎用）。"""

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            sql = payload.get("sql")
            params = payload.get("params")
            limit = int(payload.get("limit", 500))
            page = payload.get("page")
            page_size = payload.get("page_size")
            cache_ttl = int(payload.get("cache_ttl", 0))  # 秒；0 表示不缓存
            with_commentary = bool(payload.get("with_commentary", False))
            if not sql:
                return fail("Missing sql", status=400)

            if page and page_size:
                result = run_readonly_paginated(sql, params, tenant_id=tenant_id, page=int(page), page_size=int(page_size))
                rows = result["rows"]
            else:
                if cache_ttl > 0:
                    result = cached_run_readonly(sql, params, tenant_id=tenant_id, limit=limit, ttl=cache_ttl)
                else:
                    result = run_readonly(sql, params, tenant_id=tenant_id, limit=limit)
                rows = result["rows"]

            spec = suggest_spec(rows)
            out = {**result, "chart_spec": spec}

            if with_commentary:
                o = Orchestrator(tenant_id=tenant_id, agent="bi")
                preview = rows[:20]
                msg = (
                    "你是零售/医药行业 BI 分析师。\n"
                    "请用简洁中文解读数据，输出 3 条洞察与 1-2 条建议，不要复述 SQL 原文。\n"
                    f"数据预览: {preview}\n"
                    f"图表建议: {spec}\n"
                )
                ans = o.chat_once(session=None, user_message=msg)
                out.update({"llm_commentary": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})
            return ok(out)
        except ValueError as e:
            return fail(str(e), status=400)
        except Exception as e:
            return fail(str(e))