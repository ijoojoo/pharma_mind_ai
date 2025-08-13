# file: core/views/ai/bi/export.py
# purpose: 导出只读查询结果为 CSV 文件（审计友好）
from __future__ import annotations
import csv
from io import StringIO
from django.views import View
from django.http import HttpRequest, HttpResponse
from core.views.utils import fail, get_json
from core.ai.tools.sql_tool import run_readonly


class BiSqlExportCsvView(View):
    """导出 CSV：接收 {sql, params, limit?}，返回 text/csv 响应。"""

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            sql = payload.get("sql")
            params = payload.get("params")
            limit = int(payload.get("limit", 10000))
            if not sql:
                return fail("Missing sql", status=400)
            result = run_readonly(sql, params, tenant_id=tenant_id, limit=limit)
            rows = result["rows"]
            # 生成 CSV
            if not rows:
                headers = []
            else:
                headers = list(rows[0].keys())
            buf = StringIO()
            writer = csv.DictWriter(buf, fieldnames=headers)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
            data = buf.getvalue()
            resp = HttpResponse(data, content_type="text/csv; charset=utf-8")
            resp["Content-Disposition"] = "attachment; filename=bi_export.csv"
            return resp
        except ValueError as e:
            return fail(str(e), status=400)
        except Exception as e:
            return fail(str(e))
