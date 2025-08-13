# file: core/ai/rag/retriever.py
# purpose: 检索统一入口（当前使用简单文本匹配；后续可切换 pgvector 相似检索）
from __future__ import annotations
from typing import List, Dict
from core.ai.rag.vectorstore.pgvector import search as _search


def retrieve_contexts(*, tenant_id: str, query: str, top_k: int = 5, filters: dict | None = None) -> List[Dict]:
    return _search(tenant_id=tenant_id, query=query, top_k=top_k, filters=filters)
