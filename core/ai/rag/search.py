# file: core/ai/rag/search.py
# purpose: 检索服务：向量相似度（余弦）TopK + 上下文拼接；可用于回答生成
from __future__ import annotations
from typing import List, Dict, Any, Tuple
import math
from django.db.models import Prefetch

from core.models.ai_rag import AiRagDocument, AiRagChunk, AiRagEmbedding
from .embed import create_embedder


def _cosine(a: List[float], b: List[float]) -> float:
    """计算余弦相似度。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return float(dot / (na * nb))


def search_chunks(*, tenant_id: str, query: str, top_k: int = 5, provider_key: str | None = None) -> List[Dict[str, Any]]:
    """对指定租户的所有分块做相似度检索，返回 TopK 结果。"""
    emb = create_embedder(provider_key)
    qvecs, meta = emb.batch_embed([query])
    qv = qvecs[0] if qvecs else []
    # 拉取全部向量（演示用；生产应分页/ANN）
    rows = (
        AiRagEmbedding.objects
        .select_related("chunk", "chunk__document")
        .filter(chunk__document__document__tenant_id=tenant_id)  # type: ignore
    )
    scored: List[Tuple[float, AiRagEmbedding]] = []
    for e in rows:
        if e.dim != len(qv):
            continue  # 维度不匹配跳过
        score = _cosine(qv, e.vector)
        scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: List[Dict[str, Any]] = []
    for score, e in scored[: max(1, min(top_k, 50))]:
        ck = e.chunk
        doc = ck.document
        out.append({
            "score": round(float(score), 4),
            "chunk_id": ck.id,
            "document_id": doc.id,
            "title": doc.title,
            "content": ck.content,
            "meta": doc.meta,
            "tags": doc.tags,
        })
    return out


def build_context(snippets: List[Dict[str, Any]], *, max_tokens: int = 1200) -> str:
    """将若干检索片段拼接成 Prompt 上下文。"""
    buf: List[str] = []
    used = 0
    for it in snippets:
        c = it.get("content") or ""
        t = len(c) // 4
        if used + t > max_tokens:
            break
        buf.append(f"【{it.get('title') or '片段'}】\n{c}")
        used += t
    return "\n\n".join(buf)