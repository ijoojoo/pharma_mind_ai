# file: core/ai/llm/base.py
# purpose: LLM Provider 基类与工具：统一接口、错误类型、Token 估算（可选 tiktoken）
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import os


class ProviderError(Exception):
    pass


class ProviderNotConfigured(ProviderError):
    pass


@dataclass(frozen=True)
class ProviderMeta:
    key: str
    name: str
    default_model: str
    env_keys: Dict[str, str]  # e.g. {"api_key": "OPENAI_API_KEY", "base_url": "OPENAI_BASE"}


class LlmProvider(ABC):
    meta: ProviderMeta

    def __init__(self, *, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._ensure_config()

    # -- helpers --------------------------------------------------------------
    def _ensure_config(self) -> None:
        # 缺省从环境变量兜底
        if not self.api_key and self.meta.env_keys.get("api_key"):
            self.api_key = os.getenv(self.meta.env_keys["api_key"]) or None
        if not self.base_url and self.meta.env_keys.get("base_url"):
            self.base_url = os.getenv(self.meta.env_keys["base_url"]) or None
        if not self.api_key:
            raise ProviderNotConfigured(f"{self.meta.key} not configured: missing API key")

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """粗略估算 Token；若安装 tiktoken 则更精确。"""
        if not text:
            return 0
        try:
            import tiktoken  # type: ignore
            enc = tiktoken.get_encoding("cl100k_base")
            return int(len(enc.encode(text)))
        except Exception:
            # 简单估算：每 4 字符 ≈ 1 token
            return max(1, len(text) // 4)

    # -- unified chat API -----------------------------------------------------
    @abstractmethod
    def chat(self, *, messages: List[Dict[str, str]], model: Optional[str] = None, stream: bool = False, **kwargs) -> Dict[str, Any]:
        """执行对话，返回 {content, tokens_in, tokens_out, raw}；出错抛 ProviderError。
        - messages: [{role:'user'|'system'|'assistant', content:'...'}]
        - model: 可选覆盖模型名；默认用 meta.default_model
        - stream: 预留（当前统一非流式返回）
        """
        raise NotImplementedError