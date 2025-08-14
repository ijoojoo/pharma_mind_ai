# file: core/ai/llm/provider_adapter.py
# purpose: 兼容旧引用路径的过渡导出（DEPRECATED）。
# 历史代码可能 `from core.ai.llm.provider_adapter import GeminiAdapter`；
# 现在统一迁移到 `from core.ai.llm.providers import GeminiAdapter`。
# 此文件仅作过渡，便于逐步替换 import；迁移完成后可删除。

from __future__ import annotations
from core.ai.llm.providers import (
    BaseAdapter,
    ChatResult,
    GPTAdapter,
    MockAdapter,
    GeminiAdapter,
    DeepSeekAdapter,
    ZhipuAdapter,
)

__all__ = [
    "BaseAdapter",
    "ChatResult",
    "GPTAdapter",
    "MockAdapter",
    "GeminiAdapter",
    "DeepSeekAdapter",
    "ZhipuAdapter",
]