# file: core/management/commands/rag_reindex.py
# purpose: 管理命令：批量重建索引（可按 tenant/doc_id 过滤）
from __future__ import annotations
from typing import Optional
from django.core.management.base import BaseCommand
from core.ai.rag.models import AiRagDocument
from core.ai.rag.tasks import reindex_document


class Command(BaseCommand):
    help = "Reindex RAG documents"

    def add_arguments(self, parser):
        parser.add_argument("--tenant", dest="tenant_id", help="Tenant ID", default=None)
        parser.add_argument("--doc", dest="doc_id", help="Document ID", type=int, default=None)

    def handle(self, *args, **options):
        tenant_id: Optional[str] = options.get("tenant_id")
        doc_id: Optional[int] = options.get("doc_id")
        if doc_id:
            self.stdout.write(str(reindex_document(doc_id=doc_id)))
            return
        qs = AiRagDocument.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        for d in qs:
            self.stdout.write(str(reindex_document(doc_id=d.id)))
