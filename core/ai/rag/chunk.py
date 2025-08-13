# file: core/ai/rag/chunk.py
# purpose: 文本分块工具（按字符与标点启发式；估算 token）
from __future__ import annotations
from typing import List
import re

_SENT_SPLIT = re.compile(r"(?<=[。！？.!?])\s+")


def estimate_tokens(text: str) -> int:
    """粗略估算 tokens（4 字符≈1 token）。"""
    if not text:
        return 0
    return max(1, len(text) // 4)


def split_text(text: str, *, max_tokens: int = 400, hard_max_tokens: int = 800) -> List[str]:
    """将长文本拆成多个分块。
    - 先按句子切分，再合并到不超过 max_tokens；极端情况下允许到 hard_max_tokens。
    - 返回分块字符串列表。
    """
    if not text:
        return []
    sentences = _SENT_SPLIT.split(text.strip())
    chunks: List[str] = []
    buf: List[str] = []
    cur = 0
    for s in sentences:
        t = estimate_tokens(s)
        if cur + t <= max_tokens:
            buf.append(s)
            cur += t
        else:
            if buf:
                chunks.append(" ".join(buf).strip())
                buf, cur = [s], t
            else:
                # 单句过长 → 硬切
                hard_chars = (hard_max_tokens or max_tokens) * 4
                for i in range(0, len(s), hard_chars):
                    part = s[i:i + hard_chars]
                    chunks.append(part)
                buf, cur = [], 0
    if buf:
        chunks.append(" ".join(buf).strip())
    return [c for c in chunks if c]
