# file: core/views/ai/rag/urls.py
# purpose: RAG 路由（加入 docs/ 与 reindex）
from django.urls import path
from .ingest import RagIngestView
from .query import RagQueryView
from .docs import RagDocListView, RagDocDetailView, RagDocDeleteView, RagDocReindexView

urlpatterns = [
    path("ingest/", RagIngestView.as_view(), name="ai_rag_ingest"),
    path("query/", RagQueryView.as_view(), name="ai_rag_query"),
    path("docs/", RagDocListView.as_view(), name="ai_rag_docs"),
    path("docs/<int:doc_id>/", RagDocDetailView.as_view(), name="ai_rag_doc_detail"),
    path("docs/<int:doc_id>/delete/", RagDocDeleteView.as_view(), name="ai_rag_doc_delete"),
    path("docs/<int:doc_id>/reindex/", RagDocReindexView.as_view(), name="ai_rag_doc_reindex"),
]
