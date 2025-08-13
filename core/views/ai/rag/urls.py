# file: core/views/ai/rag/urls.py
# purpose: RAG 路由：/api/ai/rag/ingest/ 与 /api/ai/rag/query/
from __future__ import annotations
from django.urls import path
from .ingest import RagIngestView
from .query import RagQueryView

urlpatterns = [
    path("ingest/", RagIngestView.as_view(), name="ai_rag_ingest"),
    path("query/", RagQueryView.as_view(), name="ai_rag_query"),
]