# file: core/views/ai/rag/ingest.py
# purpose: RAG 入库接口：POST texts -> 文档/分块/向量入库；返回统计
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.rag.ingest import ingest_texts


class RagIngestView(View):
    """接收 JSON: {items:[{title,text,tags?,meta?}], source?} 并入库。"""

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            items = payload.get("items") or []
            source = payload.get("source") or "api"
            data = ingest_texts(tenant_id=tenant_id, items=items, source=source)
            return ok(data)
        except Exception as e:
            return fail(str(e))