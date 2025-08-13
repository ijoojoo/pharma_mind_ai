# file: core/ai/rag/ingest.py
# purpose: 入库服务：接收文本→分块→向量化→ORM 入库；返回统计
from __future__ import annotations
from typing import List, Dict, Any
from django.db import transaction

from core.models.ai_rag import AiRagDocument, AiRagChunk, AiRagEmbedding
from .chunk import split_text, estimate_tokens
from .embed import create_embedder


def ingest_texts(*, tenant_id: str, items: List[Dict[str, Any]], source: str = "api") -> Dict[str, Any]:
    """批量入库长文本。
    参数：
      - tenant_id: 租户
      - items: [{title, text, tags?, meta?}]
      - source: 来源标识（默认 api）
    返回：{"docs": n, "chunks": m, "embeddings": k}
    """
    emb = create_embedder()
    total_docs = total_chunks = total_vecs = 0
    for it in items or []:
        title = (it.get("title") or "").strip()
        text = (it.get("text") or "").strip()
        if not text:
            continue
        tags = (it.get("tags") or "").strip()
        meta = it.get("meta") or {}
        with transaction.atomic():
            doc = AiRagDocument.objects.create(
                tenant_id=tenant_id,
                source=source,
                title=title[:255],
                tags=tags[:255],
                meta=meta,
            )
            # 分块
            parts = split_text(text)
            chunks = []
            for i, c in enumerate(parts):
                ck = AiRagChunk.objects.create(document=doc, ordinal=i, content=c, token_count=estimate_tokens(c))
                chunks.append(ck)
            total_docs += 1
            total_chunks += len(chunks)
            # 向量化
            vecs, meta_emb = emb.batch_embed([c.content for c in chunks])
            for ck, v in zip(chunks, vecs):
                AiRagEmbedding.objects.create(
                    chunk=ck,
                    provider_key=str(meta_emb.get("provider")),
                    model=str(meta_emb.get("model")),
                    dim=int(meta_emb.get("dim") or len(v)),
                    vector=v,
                )
            total_vecs += len(vecs)
    return {"docs": total_docs, "chunks": total_chunks, "embeddings": total_vecs}