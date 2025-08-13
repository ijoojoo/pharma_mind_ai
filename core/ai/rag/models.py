# file: core/ai/rag/models.py
# purpose: RAG 文档与分片 ORM（MVP：文本+JSON 向量；后续可接 pgvector 专用表）
from __future__ import annotations
from django.db import models


class AiRagDocument(models.Model):
    tenant_id = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255)
    filename = models.CharField(max_length=255, blank=True, default="")
    source = models.CharField(max_length=64, blank=True, default="upload")  # upload/url/api
    content_hash = models.CharField(max_length=64, db_index=True)  # sha256
    status = models.CharField(max_length=32, default="ready")  # ready/processing/failed
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_rag_document"
        indexes = [models.Index(fields=["tenant_id", "updated_at"])]

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.title}"


class AiRagChunk(models.Model):
    doc = models.ForeignKey(AiRagDocument, on_delete=models.CASCADE, related_name="chunks")
    tenant_id = models.CharField(max_length=64, db_index=True)
    ordinal = models.IntegerField(default=0)
    text = models.TextField()
    embedding = models.JSONField(default=list, blank=True)  # [float, ...] 维度后续统一
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_rag_chunk"
        indexes = [
            models.Index(fields=["tenant_id", "ordinal"]),
            models.Index(fields=["doc", "ordinal"]),
        ]
