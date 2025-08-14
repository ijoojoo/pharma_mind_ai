# file: core/ai/llm/__init__.py
# purpose: 顶层 LLM 包导出入口（不含二级目录的实现）。
# 作用：对外统一导出注册表方法（normalize_provider_key/has_provider/list_providers/get_provider_meta）
#     以及常用适配器（GPT/Mock/Gemini/DeepSeek/智谱）以便直接 import 使用。

from __future__ import annotations

# --- 注册表 API（供设置/偏好解析等使用） ---
from .registry import (
    ProviderMeta,
    normalize_provider_key,
    has_provider,
    get_provider_meta,
    list_providers,
    get_adapter_class,
)

# --- 常用适配器（来自二级目录 providers 包；便于直接导入使用） ---
from core.ai.llm.providers import (
    GPTAdapter,
    MockAdapter,
    GeminiAdapter,
    DeepSeekAdapter,
    ZhipuAdapter,
)

__all__ = [
    # registry
    "ProviderMeta",
    "normalize_provider_key",
    "has_provider",
    "get_provider_meta",
    "list_providers",
    "get_adapter_class",
    # adapters
    "GPTAdapter",
    "MockAdapter",
    "GeminiAdapter",
    "DeepSeekAdapter",
    "ZhipuAdapter",
]