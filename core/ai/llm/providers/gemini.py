# file: core/ai/llm/providers/gemini.py
# purpose: Google Gemini 适配；读取 GOOGLE_API_KEY；使用 v1beta generateContent 接口
from __future__ import annotations
from typing import Any, Dict, List, Optional
import requests
from ..base import LlmProvider, ProviderMeta, ProviderError


class GeminiProvider(LlmProvider):
    meta = ProviderMeta(
        key="gemini",
        name="Google Gemini",
        default_model="gemini-1.5-pro",
        env_keys={"api_key": "GOOGLE_API_KEY", "base_url": "GOOGLE_API_BASE"},
    )

    def chat(self, *, messages: List[Dict[str, str]], model: Optional[str] = None, stream: bool = False, **kwargs) -> Dict[str, Any]:
        m = model or self.meta.default_model
        base = (self.base_url or "https://generativelanguage.googleapis.com").rstrip("/")
        url = f"{base}/v1beta/models/{m}:generateContent?key={self.api_key}"
        # 将 messages 合并为单 prompt（简单化处理）
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            parts.append({"text": f"[{role}] {msg.get('content','')}"})
        payload = {"contents": [{"parts": parts}]}
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            if r.status_code >= 400:
                raise ProviderError(f"gemini http {r.status_code}: {r.text[:200]}")
            data = r.json()
            candidates = data.get("candidates") or []
            content = ""
            if candidates and candidates[0].get("content", {}).get("parts"):
                content = "".join(p.get("text", "") for p in candidates[0]["content"]["parts"])
            tokens_in = self.estimate_tokens(str(messages))
            tokens_out = self.estimate_tokens(content)
            return {"content": content, "tokens_in": tokens_in, "tokens_out": tokens_out, "raw": data}
        except requests.RequestException as e:
            raise ProviderError(str(e))