# file: core/ai/llm/providers/zhipu.py
# purpose: 智谱 GLM 适配；读取 ZHIPU_API_KEY；v4 chat completions
from __future__ import annotations
from typing import Any, Dict, List, Optional
import requests
from ..base import LlmProvider, ProviderMeta, ProviderError


class ZhipuProvider(LlmProvider):
    meta = ProviderMeta(
        key="zhipu",
        name="Zhipu GLM",
        default_model="glm-4",
        env_keys={"api_key": "ZHIPU_API_KEY", "base_url": "ZHIPU_API_BASE"},
    )

    def chat(self, *, messages: List[Dict[str, str]], model: Optional[str] = None, stream: bool = False, **kwargs) -> Dict[str, Any]:
        base = (self.base_url or "https://open.bigmodel.cn").rstrip("/")
        url = f"{base}/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": model or self.meta.default_model, "messages": messages, "stream": False}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if r.status_code >= 400:
                raise ProviderError(f"zhipu http {r.status_code}: {r.text[:200]}")
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            tokens_in = int(usage.get("prompt_tokens") or 0) or self.estimate_tokens(str(messages))
            tokens_out = int(usage.get("completion_tokens") or 0) or self.estimate_tokens(content)
            return {"content": content, "tokens_in": tokens_in, "tokens_out": tokens_out, "raw": data}
        except requests.RequestException as e:
            raise ProviderError(str(e))