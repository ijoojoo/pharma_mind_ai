# file: core/views/ai/bi/urls.py
# purpose: BI 路由：自然语言问答 + 直接 SQL 执行 + 导出
from __future__ import annotations
from django.urls import path
from .nlp_query import BiNlpQueryView
from .exec import BiSqlExecView
from .export import BiSqlExportCsvView

urlpatterns = [
    path("query/", BiNlpQueryView.as_view(), name="ai_bi_query"),
    path("exec/", BiSqlExecView.as_view(), name="ai_bi_exec"),
    path("export/csv/", BiSqlExportCsvView.as_view(), name="ai_bi_export_csv"),
]