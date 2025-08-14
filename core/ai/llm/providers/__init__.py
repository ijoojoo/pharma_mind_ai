# file: core/ai/llm/providers/__init__.py
# purpose: providers 包的聚合出口：统一导出基类与各供应商适配器；包含 gpt/mock/gemini/deepseek/zhipu
# 注意：若历史存在同名单文件 core/ai/llm/providers.py，请删除以避免与包冲突

from __future__ import annotations
from .base import BaseAdapter, ChatResult
from .gpt import GPTAdapter
from .mock import MockAdapter
from .gemini import GeminiAdapter
from .deepseek import DeepSeekAdapter
from .zhipu import ZhipuAdapter

__all__ = [
    "BaseAdapter",
    "ChatResult",
    "GPTAdapter",
    "MockAdapter",
    "GeminiAdapter",
    "DeepSeekAdapter",
    "ZhipuAdapter",
]
