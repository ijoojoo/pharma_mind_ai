# file: core/ai/llm/registry.py
# purpose: Provider 注册表与工厂；提供 normalize_provider_key/has_provider/get_provider_meta/list_providers/create_provider
from __future__ import annotations
from typing import Dict, Callable, Any, List
from dataclasses import dataclass
from .base import ProviderMeta, LlmProvider, ProviderNotConfigured
from .providers.mock import MockProvider
from .providers.gpt import GptProvider
from .providers.gemini import GeminiProvider
from .providers.deepseek import DeepseekProvider
from .providers.zhipu import ZhipuProvider


@dataclass(frozen=True)
class _Entry:
    meta: ProviderMeta
    factory: Callable[..., LlmProvider]


_REGISTRY: Dict[str, _Entry] = {
    "mock": _Entry(MockProvider.meta, lambda **kw: MockProvider(**kw)),
    "gpt": _Entry(GptProvider.meta, lambda **kw: GptProvider(**kw)),
    "gemini": _Entry(GeminiProvider.meta, lambda **kw: GeminiProvider(**kw)),
    "deepseek": _Entry(DeepseekProvider.meta, lambda **kw: DeepseekProvider(**kw)),
    "zhipu": _Entry(ZhipuProvider.meta, lambda **kw: ZhipuProvider(**kw)),
}

# 别名映射
_ALIASES = {
    "openai": "gpt",
    "chatgpt": "gpt",
    "glm": "zhipu",
}


def normalize_provider_key(name: str | None) -> str | None:
    if not name:
        return None
    key = str(name).strip().lower()
    return _ALIASES.get(key, key)


def has_provider(key: str | None) -> bool:
    return bool(key and normalize_provider_key(key) in _REGISTRY)


def get_provider_meta(key: str) -> ProviderMeta:
    k = normalize_provider_key(key)
    if not k or k not in _REGISTRY:
        raise KeyError(f"unknown provider: {key}")
    return _REGISTRY[k].meta


def list_providers() -> List[dict]:
    out = []
    for k, e in _REGISTRY.items():
        out.append({"key": e.meta.key, "name": e.meta.name, "default_model": e.meta.default_model})
    return out


def create_provider(key: str, **kwargs) -> LlmProvider:
    k = normalize_provider_key(key)
    if not k or k not in _REGISTRY:
        raise KeyError(f"unknown provider: {key}")
    entry = _REGISTRY[k]
    return entry.factory(**kwargs)


__all__ = [
    "normalize_provider_key", "has_provider", "get_provider_meta", "list_providers", "create_provider",
]

