# file: core/ai/llm/provider_adapter.py
# purpose: 统一选择并创建 LLM Client；按租户/用户的“有效模型”定向到具体 Provider
from __future__ import annotations
import os
from typing import List, Optional, Tuple
from core.ai.llm.base import LlmClient, ChatMessage, ChatResult
from core.ai.settings import get_effective_model
from core.ai.llm.registry import normalize_provider_key
from core.ai.llm.providers.gpt import GPT5Client
from core.ai.llm.providers.gemini import GeminiClient
from core.ai.llm.providers.deepseek import DeepseekClient
from core.ai.llm.providers.zhipu import ZhipuClient


class _ClientCache:
    _cache: dict[str, LlmClient] = {}

    @classmethod
    def get(cls, key: str, factory):
        if key not in cls._cache:
            cls._cache[key] = factory()
        return cls._cache[key]


def _build_client(provider_key: str) -> LlmClient:
    key = normalize_provider_key(provider_key) or "mock"
    if key == "gpt5":
        return _ClientCache.get("gpt5", lambda: GPT5Client())
    if key == "gemini":
        return _ClientCache.get("gemini", lambda: GeminiClient())
    if key == "deepseek":
        return _ClientCache.get("deepseek", lambda: DeepseekClient())
    if key == "zhipu":
        return _ClientCache.get("zhipu", lambda: ZhipuClient())
    # 默认回退：使用 GPT5Client 的 base_url + mock model，或直接用轻量 mock（此处用 GPT5 以复用 token 估算）
    return _ClientCache.get("gpt5", lambda: GPT5Client(default_model=os.getenv("OPENAI_MODEL", "gpt-4o")))


def get_llm_client(env_provider: Optional[str] = None) -> LlmClient:
    return _build_client(env_provider or os.getenv("LLM_PROVIDER", "gpt5"))


def get_llm_client_for(tenant_id: str, user_id: Optional[str] = None, env_provider: Optional[str] = None) -> Tuple[LlmClient, dict]:
    eff = get_effective_model(tenant_id=tenant_id, user_id=user_id, env_provider=env_provider)
    return _build_client(eff.provider), eff.to_dict()
