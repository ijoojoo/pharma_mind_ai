# file: core/views/ai/rag/docs.py
# purpose: 文档列表/详情/删除/重建索引
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail
from core.ai.rag.models import AiRagDocument
from core.ai.rag.tasks import reindex_document


class RagDocListView(View):
    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            limit = int(request.GET.get("limit", 20))
            offset = int(request.GET.get("offset", 0))
            qs = AiRagDocument.objects.filter(tenant_id=tenant_id).order_by("-updated_at")[offset : offset + limit]
            items = [
                {
                    "id": d.id,
                    "title": d.title,
                    "filename": d.filename,
                    "status": d.status,
                    "updated_at": d.updated_at,
                }
                for d in qs
            ]
            return ok({"items": items, "offset": offset, "limit": limit})
        except Exception as e:
            return fail(str(e))


class RagDocDetailView(View):
    def get(self, request: HttpRequest, doc_id: int):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            d = AiRagDocument.objects.filter(id=doc_id, tenant_id=tenant_id).first()
            if not d:
                return fail("Document not found", status=404)
            return ok(
                {
                    "id": d.id,
                    "title": d.title,
                    "filename": d.filename,
                    "status": d.status,
                    "meta": d.meta,
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                }
            )
        except Exception as e:
            return fail(str(e))


class RagDocDeleteView(View):
    def delete(self, request: HttpRequest, doc_id: int):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            d = AiRagDocument.objects.filter(id=doc_id, tenant_id=tenant_id).first()
            if not d:
                return fail("Document not found", status=404)
            d.delete()
            return ok({"deleted": True})
        except Exception as e:
            return fail(str(e))


class RagDocReindexView(View):
    def post(self, request: HttpRequest, doc_id: int):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.POST.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            d = AiRagDocument.objects.filter(id=doc_id, tenant_id=tenant_id).first()
            if not d:
                return fail("Document not found", status=404)
            res = reindex_document(doc_id=doc_id)
            return ok(res)
        except Exception as e:
            return fail(str(e))

