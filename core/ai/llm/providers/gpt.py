# file: core/ai/llm/providers/gpt.py
# purpose: GPT（OpenAI 兼容）适配器；通过 HTTP 调用 /v1/chat/completions，统一返回 ChatResult 所需字段
# 用途：作为系统默认的通用提供商（provider_key = "gpt"），支持自定义 base_url 与模型名
# 依赖：环境变量 OPENAI_API_KEY；可选 OPENAI_BASE_URL（默认 https://api.openai.com/v1）、GPT_MODEL

from __future__ import annotations
import os
import requests
from typing import Any, Dict
from .base import BaseAdapter


class GPTAdapter(BaseAdapter):
    """GPT 驱动（OpenAI Chat Completions 兼容）。
    - 使用 `OPENAI_API_KEY` 作为鉴权；
    - `OPENAI_BASE_URL` 可指向兼容代理；
    - 模型名默认取 `GPT_MODEL` 或回退到 "gpt-4o-mini"。
    """

    provider = "gpt"
    default_model = os.getenv("GPT_MODEL", "gpt-4o-mini")

    def __init__(self, **kw):
        """初始化：读取 base_url/api_key/model。"""
        super().__init__(api_key=kw.get("api_key") or os.getenv("OPENAI_API_KEY"), model=kw.get("model"))
        self.base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def _chat_impl(self, prompt: str) -> Dict[str, Any]:
        """调用 /chat/completions 并规范化响应。"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        url = f"{self.base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        r.raise_for_status()
        obj = r.json()
        choice = (obj.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content", "")
        usage = obj.get("usage") or {}
        return {
            "content": content,
            "tokens_in": int(usage.get("prompt_tokens") or 0),
            "tokens_out": int(usage.get("completion_tokens") or 0),
            "raw": obj,
        }


