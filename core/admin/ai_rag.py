# file: core/admin/ai_rag.py
# purpose: Admin 注册 RAG 三个模型，便于排错与手工管理
from __future__ import annotations
from django.contrib import admin
from core.models.ai_rag import AiRagDocument, AiRagChunk, AiRagEmbedding


@admin.register(AiRagDocument)
class AiRagDocumentAdmin(admin.ModelAdmin):
    """文档维度：支持按租户过滤与标题搜索。"""
    list_display = ("id", "tenant_id", "title", "source", "status", "updated_at")
    search_fields = ("tenant_id", "title", "tags")
    list_filter = ("source", "status")


@admin.register(AiRagChunk)
class AiRagChunkAdmin(admin.ModelAdmin):
    """分块维度：展示 token 数与所属文档。"""
    list_display = ("id", "document", "ordinal", "token_count", "created_at")
    search_fields = ("document__tenant_id", "document__title")


@admin.register(AiRagEmbedding)
class AiRagEmbeddingAdmin(admin.ModelAdmin):
    """向量维度：查看 provider/model 与维度。"""
    list_display = ("id", "chunk", "provider_key", "model", "dim", "created_at")
    search_fields = ("chunk__document__tenant_id", "provider_key", "model")
