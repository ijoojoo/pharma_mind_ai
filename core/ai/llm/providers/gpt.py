# file: core/ai/llm/providers/gpt.py
# purpose: GPT5（OpenAI 风格 API）适配；默认读取 OPENAI_API_KEY / OPENAI_BASE
from __future__ import annotations
from typing import Any, Dict, List, Optional
import requests
from ..base import LlmProvider, ProviderMeta, ProviderError


class GptProvider(LlmProvider):
    meta = ProviderMeta(
        key="gpt5",
        name="GPT5 (OpenAI-compatible)",
        default_model="gpt-5.1-mini",
        env_keys={"api_key": "OPENAI_API_KEY", "base_url": "OPENAI_BASE"},
    )

    def chat(self, *, messages: List[Dict[str, str]], model: Optional[str] = None, stream: bool = False, **kwargs) -> Dict[str, Any]:
        base = (self.base_url or "https://api.openai.com").rstrip("/")
        url = f"{base}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: Dict[str, Any] = {
            "model": model or self.meta.default_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
            "stream": False,
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if r.status_code >= 400:
                raise ProviderError(f"gpt5 http {r.status_code}: {r.text[:200]}")
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            tokens_in = int(usage.get("prompt_tokens") or 0) or self.estimate_tokens(str(messages))
            tokens_out = int(usage.get("completion_tokens") or 0) or self.estimate_tokens(content)
            return {"content": content, "tokens_in": tokens_in, "tokens_out": tokens_out, "raw": data}
        except requests.RequestException as e:
            raise ProviderError(str(e))