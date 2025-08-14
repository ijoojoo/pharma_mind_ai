# file: core/ai/llm/providers/zhipu.py
# purpose: 智谱 GLM 适配器：调用 `/api/paas/v4/chat/completions`，标准化输出以便统一计费与审计。

from __future__ import annotations
import os
import requests
from typing import Any, Dict
from .base import BaseAdapter


class ZhipuAdapter(BaseAdapter):
    """智谱 GLM 适配器：把响应统一到 ChatResult 所需的字段。"""

    provider = "zhipu"
    default_model = os.getenv("ZHIPU_MODEL", "glm-4")

    def __init__(self, **kw):
        """从环境或传参读取 base_url/api_key/model。"""
        super().__init__(api_key=kw.get("api_key") or os.getenv("ZHIPU_API_KEY"), model=kw.get("model"))
        self.base = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn")

    def _chat_impl(self, prompt: str) -> Dict[str, Any]:
        """调用智谱 HTTP API 并返回标准化结构。"""
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY is required")
        url = f"{self.base}/api/paas/v4/chat/completions"
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
