# file: core/ai/llm/providers/deepseek.py
# purpose: DeepSeek 适配；读取 DEEPSEEK_API_KEY；OpenAI 风格
from __future__ import annotations
from typing import Any, Dict, List, Optional
import requests
from ..base import LlmProvider, ProviderMeta, ProviderError


class DeepseekProvider(LlmProvider):
    meta = ProviderMeta(
        key="deepseek",
        name="DeepSeek",
        default_model="deepseek-chat",
        env_keys={"api_key": "DEEPSEEK_API_KEY", "base_url": "DEEPSEEK_API_BASE"},
    )

    def chat(self, *, messages: List[Dict[str, str]], model: Optional[str] = None, stream: bool = False, **kwargs) -> Dict[str, Any]:
        base = (self.base_url or "https://api.deepseek.com").rstrip("/")
        url = f"{base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": model or self.meta.default_model, "messages": messages, "stream": False}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if r.status_code >= 400:
                raise ProviderError(f"deepseek http {r.status_code}: {r.text[:200]}")
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            tokens_in = int(usage.get("prompt_tokens") or 0) or self.estimate_tokens(str(messages))
            tokens_out = int(usage.get("completion_tokens") or 0) or self.estimate_tokens(content)
            return {"content": content, "tokens_in": tokens_in, "tokens_out": tokens_out, "raw": data}
        except requests.RequestException as e:
            raise ProviderError(str(e))
