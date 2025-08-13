# file: core/ai/rag/vectorstore/pgvector.py
# purpose: 向量存取/检索占位（无 pgvector 依赖时回退为简单文本匹配）
from __future__ import annotations
from typing import List, Dict, Sequence
from django.db.models.functions import Length
from core.ai.rag.models import AiRagChunk


# NOTE: 真实环境建议使用 pgvector + 余弦相似度检索；
# 这里先提供占位：简单 ILIKE 匹配 + 文本长度排序。

def upsert_chunks(doc_id: int, chunks: Sequence[dict]) -> List[int]:
    ids: List[int] = []
    for c in chunks:
        row = AiRagChunk.objects.create(
            doc_id=doc_id,
            tenant_id=c["tenant_id"],
            ordinal=c["ordinal"],
            text=c["text"],
            embedding=c.get("embedding", []),
            meta=c.get("meta", {}),
        )
        ids.append(row.id)
    return ids


def search(*, tenant_id: str, query: str, top_k: int = 5, filters: dict | None = None) -> List[Dict]:
    qs = AiRagChunk.objects.filter(tenant_id=tenant_id)
    if query:
        qs = qs.filter(text__icontains=query)
    # 允许 filters 扩展（如按 doc_id 过滤）
    if filters:
        if "doc_id" in filters:
            qs = qs.filter(doc_id=filters["doc_id"])
    qs = qs.annotate(tlen=Length("text")).order_by("tlen")[: max(1, top_k)]
    rows = list(qs.select_related("doc"))
    return [
        {
            "chunk_id": r.id,
            "doc_id": r.doc_id,
            "text": r.text,
            "meta": r.meta,
            "doc": {
                "title": r.doc.title,
                "filename": r.doc.filename,
                "source": r.doc.source,
            },
        }
        for r in rows
    ]

