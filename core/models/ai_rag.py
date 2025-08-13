# file: core/models/ai_rag.py
# purpose: RAG 相关 ORM 模型（文档、分块、向量）；用于入库与检索
from __future__ import annotations
from django.db import models
from django.utils import timezone


class AiRagDocument(models.Model):
    """存放原始文档（或一段长文本）的元数据与归属。"""
    tenant_id = models.CharField(max_length=64, db_index=True, help_text="多租户隔离标识")
    source = models.CharField(max_length=64, default="api", help_text="来源（api/upload/crawl/...）")
    title = models.CharField(max_length=255, blank=True, default="", help_text="标题或摘要")
    tags = models.CharField(max_length=255, blank=True, default="", help_text="逗号分隔标签")
    meta = models.JSONField(default=dict, blank=True, help_text="自定义元数据")
    status = models.CharField(max_length=32, default="ready", help_text="状态：ready/disabled")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_rag_document"
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
        ]

    def __str__(self) -> str:  # noqa: D401
        """返回易读名称。"""
        return f"Doc<{self.id}:{self.title[:20]}>"


class AiRagChunk(models.Model):
    """文档的分块文本（便于向量化与检索）。"""
    document = models.ForeignKey(AiRagDocument, on_delete=models.CASCADE, related_name="chunks")
    ordinal = models.IntegerField(default=0, help_text="在原文档中的顺序（从0开始）")
    content = models.TextField(help_text="分块后的纯文本内容")
    token_count = models.IntegerField(default=0, help_text="估算 token 数（用于限额与调优）")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ai_rag_chunk"
        indexes = [
            models.Index(fields=["document", "ordinal"]),
        ]


class AiRagEmbedding(models.Model):
    """每个分块的一组向量（可支持不同 provider 与维度共存）。"""
    chunk = models.ForeignKey(AiRagChunk, on_delete=models.CASCADE, related_name="embeddings")
    provider_key = models.CharField(max_length=32, help_text="向量提供商，如 local/gpt/zhipu")
    model = models.CharField(max_length=64, help_text="具体向量模型名")
    dim = models.IntegerField(help_text="向量维度")
    vector = models.JSONField(help_text="浮点数组（长度等于 dim）")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ai_rag_embedding"
        indexes = [
            models.Index(fields=["chunk", "provider_key", "model"]),
        ]
