# file: core/ai/llm/providers/gemini.py
# purpose: Google Gemini 适配器：调用 generateContent API，抽取文本与用量并标准化返回。

from __future__ import annotations
import os
import requests
from typing import Any, Dict
from .base import BaseAdapter


class GeminiAdapter(BaseAdapter):
    """Google Gemini 适配器：适配 `generateContent` 接口。"""

    provider = "gemini"
    default_model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")

    def __init__(self, **kw):
        """从环境或传参读取 base_url/api_key/model，便于不同环境覆盖。"""
        super().__init__(api_key=kw.get("api_key") or os.getenv("GEMINI_API_KEY"), model=kw.get("model"))
        self.base = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")

    def _chat_impl(self, prompt: str) -> Dict[str, Any]:
        """调用 Gemini 的 HTTP API 并返回标准化结构。"""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        url = f"{self.base}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        obj = r.json()
        # 文本抽取
        text = ""
        try:
            cands = obj.get("candidates") or []
            parts = (cands[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts)
        except Exception:
            text = obj.get("text") or ""
        usage = obj.get("usageMetadata") or {}
        return {
            "content": text,
            "tokens_in": int(usage.get("promptTokenCount") or 0),
            "tokens_out": int(usage.get("candidatesTokenCount") or 0),
            "raw": obj,
        }


