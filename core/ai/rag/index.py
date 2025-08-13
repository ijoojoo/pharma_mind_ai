# file: core/ai/rag/index.py
# purpose: 文档入库/重建索引占位（MVP：仅回传接收状态与生成的 doc_id，不做持久化）
from __future__ import annotations
import uuid
from typing import Optional


def ingest_document(*, tenant_id: str, filename: str, content_bytes: bytes, domain: Optional[str] = None, tags: Optional[list[str]] = None) -> dict:
    doc_id = uuid.uuid4().hex
    size = len(content_bytes or b"")
    # TODO: 切片 + 向量化 + 持久化
    return {"doc_id": doc_id, "filename": filename, "size": size, "domain": domain, "tags": tags or [], "status": "accepted"}


def reindex_document(*, tenant_id: str, doc_id: str) -> dict:
    # TODO: 重建索引
    return {"doc_id": doc_id, "status": "reindexed"}

