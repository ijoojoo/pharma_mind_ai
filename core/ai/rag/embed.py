# file: core/ai/rag/embed.py
# purpose: 向量化提供商（gpt/本地hash/zhipu 可扩展）；create_embedder() 工厂
from __future__ import annotations
from typing import List, Tuple, Optional
import os
import math
import hashlib

try:  # 可选：网络调用
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


class BaseEmbedder:
    """向量化基类：实现 batch_embed() 并返回 (vectors, meta)。"""

    key = "base"
    default_model = "-"
    dim = 0

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def batch_embed(self, texts: List[str]) -> Tuple[List[List[float]], dict]:  # noqa: D401
        """对一组文本做向量化，返回 (向量二维数组, 附加元数据)。"""
        raise NotImplementedError


class LocalHashEmbedder(BaseEmbedder):
    """本地 Hash 向量器（无依赖、可用性优先）。
    - 使用 hashing trick 将 token（按空格/中英文混合）投影到固定维度（默认 384）。
    - 归一化为单位向量；适合作为缺省方案或离线开发环境。"""

    key = "local"
    default_model = "hash-384"

    def __init__(self, dim: int = 384, timeout: int = 5):
        super().__init__(timeout=timeout)
        self.dim = int(dim)

    @staticmethod
    def _tokenize(s: str) -> List[str]:
        return [t for t in list(s) if not t.isspace()]  # 朴素：按字符

    def batch_embed(self, texts: List[str]) -> Tuple[List[List[float]], dict]:
        vecs: List[List[float]] = []
        for text in texts:
            buckets = [0.0] * self.dim
            for tok in self._tokenize(text or ""):
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dim
                sign = 1.0 if (h >> 1) & 1 else -1.0
                buckets[idx] += sign
            # 归一化
            norm = math.sqrt(sum(x * x for x in buckets)) or 1.0
            vecs.append([x / norm for x in buckets])
        return vecs, {"provider": self.key, "model": self.default_model, "dim": self.dim}


class GptEmbedder(BaseEmbedder):
    """OpenAI 兼容 embedding 实现（需环境变量 OPENAI_API_KEY）。"""

    key = "gpt"
    default_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    dim = 1536

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        super().__init__(timeout=timeout)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE") or "https://api.openai.com").rstrip("/")

    def batch_embed(self, texts: List[str]) -> Tuple[List[List[float]], dict]:
        if not self.api_key or not requests:
            # 回退到本地
            return LocalHashEmbedder().batch_embed(texts)
        url = f"{self.base_url}/v1/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.default_model, "input": texts}
        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        if r.status_code >= 400:
            # 出错回退
            return LocalHashEmbedder().batch_embed(texts)
        data = r.json()
        vecs = [it.get("embedding", []) for it in (data.get("data") or [])]
        meta = {"provider": self.key, "model": self.default_model, "dim": len(vecs[0]) if vecs else self.dim}
        return vecs, meta


def create_embedder(key: Optional[str] = None) -> BaseEmbedder:
    """工厂：根据 key 返回向量器，默认 local；支持 gpt。"""
    name = (key or os.getenv("LLM_EMBED_PROVIDER") or "local").strip().lower()
    if name == "gpt":
        return GptEmbedder()
    return LocalHashEmbedder()