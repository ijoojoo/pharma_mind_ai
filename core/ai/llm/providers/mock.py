# file: core/ai/llm/providers/mock.py
# purpose: 本地开发/测试使用的 Mock 适配器；不依赖外部网络，按字符数估算 tokens
# 用途：作为回退 provider（provider_key = "mock"），在无 API Key 或离线模式下可用

from __future__ import annotations
from typing import Any, Dict
from .base import BaseAdapter, _estimate_tokens


class MockAdapter(BaseAdapter):
    """Mock 驱动：回显用户输入，便于联调与离线测试。"""

    provider = "mock"
    default_model = "mock-echo"

    def _chat_impl(self, prompt: str) -> Dict[str, Any]:
        """返回简单回显内容，并按字符长度估算 tokens。"""
        content = f"[mock] echo: {prompt[:2000]}"
        ti = _estimate_tokens(prompt)
        to = _estimate_tokens(content)
        return {
            "content": content,
            "tokens_in": ti,
            "tokens_out": to,
            "raw": {"mock": True},
        }

