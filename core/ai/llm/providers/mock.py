# file: core/ai/llm/providers/mock.py
# purpose: Mock 提供商（开发/测试用）；可在无 API Key 环境下工作
from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..base import LlmProvider, ProviderMeta


class MockProvider(LlmProvider):
    meta = ProviderMeta(
        key="mock",
        name="Mock",
        default_model="mock-001",
        env_keys={},
    )

    def _ensure_config(self) -> None:
        # mock 不需要配置
        return None

    def chat(self, *, messages: List[Dict[str, str]], model: Optional[str] = None, stream: bool = False, **kwargs) -> Dict[str, Any]:
        user_parts = [m.get("content", "") for m in messages if m.get("role") == "user"]
        text = "\n".join(user_parts).strip()
        content = f"[mock:{model or self.meta.default_model}] {text[:200]}"
        tokens_in = self.estimate_tokens(text)
        tokens_out = self.estimate_tokens(content)
        return {"content": content, "tokens_in": tokens_in, "tokens_out": tokens_out, "raw": {"provider": "mock"}}
