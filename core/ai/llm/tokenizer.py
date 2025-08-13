# file: core/ai/llm/tokenizer.py
# purpose: Token 估算工具；优先使用第三方分词器（若可用），否则按字符近似
from __future__ import annotations
from typing import List, Optional


def _approx_tokens_from_text(text: str) -> int:
    if not text:
        return 0
    # 英文平均 3~4 字符 = 1 token；中文近似 1~2 字 = 1 token，这里统一取 4 做保守估计
    return max(1, len(text) // 4)


def count_tokens_from_messages(messages: List[dict], model: Optional[str] = None) -> int:
    try:
        # 可选：tiktoken / gptoken / anthropic_tokenizer 等
        import tiktoken  # type: ignore

        enc = None
        if model:
            try:
                enc = tiktoken.encoding_for_model(model)
            except Exception:
                enc = tiktoken.get_encoding("cl100k_base")
        else:
            enc = tiktoken.get_encoding("cl100k_base")
        total = 0
        for m in messages:
            total += len(enc.encode(m.get("content", ""))) + 4  # role/name 开销粗略 +4
        return max(1, total)
    except Exception:
        # 回退近似
        return sum(_approx_tokens_from_text(m.get("content", "")) + 1 for m in messages)


def count_tokens_from_text(text: str, model: Optional[str] = None) -> int:
    try:
        import tiktoken  # type: ignore

        enc = None
        if model:
            try:
                enc = tiktoken.encoding_for_model(model)
            except Exception:
                enc = tiktoken.get_encoding("cl100k_base")
        else:
            enc = tiktoken.get_encoding("cl100k_base")
        return max(1, len(enc.encode(text or "")))
    except Exception:
        return _approx_tokens_from_text(text or "")

