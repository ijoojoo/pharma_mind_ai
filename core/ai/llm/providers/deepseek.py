# file: core/ai/llm/providers/deepseek.py
# purpose: DeepSeek 适配器：使用 OpenAI 兼容的 `/chat/completions` 接口，标准化输出。

from __future__ import annotations
import os
import requests
from typing import Any, Dict
from .base import BaseAdapter


class DeepSeekAdapter(BaseAdapter):
    """DeepSeek 适配器：兼容 OpenAI Chat Completions 的调用与 usage 字段。"""

    provider = "deepseek"
    default_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    def __init__(self, **kw):
        """从环境或传参读取 base_url/api_key/model。"""
        super().__init__(api_key=kw.get("api_key") or os.getenv("DEEPSEEK_API_KEY"), model=kw.get("model"))
        self.base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    def _chat_impl(self, prompt: str) -> Dict[str, Any]:
        """调用 DeepSeek API 并返回标准化结构。"""
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")
        url = f"{self.base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        r.raise_for_status()
        obj = r.json()
        choice = (obj.get("choices") or [{}])[0]
        msg = (choice.get("message") or {}).get("content", "")
        usage = obj.get("usage") or {}
        return {
            "content": msg,
            "tokens_in": int(usage.get("prompt_tokens") or 0),
            "tokens_out": int(usage.get("completion_tokens") or 0),
            "raw": obj,
        }


