# file: core/ai/rag/tasks.py
# purpose: 文档入库与重建索引（同步实现；后续可迁移到 Celery）
from __future__ import annotations
import hashlib
from typing import Optional, List
from django.db import transaction
from core.ai.rag.models import AiRagDocument
from core.ai.rag.chunking import chunk_text
from core.ai.rag.vectorstore.pgvector import upsert_chunks


@transaction.atomic
def ingest_document_bytes(*, tenant_id: str, filename: str, content_bytes: bytes, domain: Optional[str] = None, tags: Optional[list[str]] = None) -> dict:
    content = (content_bytes or b"").decode("utf-8", errors="ignore")
    h = hashlib.sha256(content_bytes or b"").hexdigest()
    title = filename or (content[:32] + "...")
    doc = AiRagDocument.objects.create(
        tenant_id=tenant_id,
        title=title,
        filename=filename,
        source="upload",
        content_hash=h,
        status="processing",
        meta={"domain": domain, "tags": tags or []},
    )
    chunks = chunk_text(content)
    payload = [
        {"tenant_id": tenant_id, "ordinal": i, "text": t, "meta": {"hash": h}}
        for i, t in enumerate(chunks)
    ]
    upsert_chunks(doc.id, payload)
    doc.status = "ready"
    doc.save(update_fields=["status"])
    return {"doc_id": doc.id, "chunks": len(payload), "status": doc.status}


@transaction.atomic
def reindex_document(*, doc_id: int) -> dict:
    doc = AiRagDocument.objects.filter(id=doc_id).first()
    if not doc:
        return {"doc_id": doc_id, "status": "not_found"}
    # 这里的重建仅标记时间，实际向量重建留待后续
    doc.status = "ready"
    doc.save(update_fields=["status"])
    return {"doc_id": doc.id, "status": doc.status}

