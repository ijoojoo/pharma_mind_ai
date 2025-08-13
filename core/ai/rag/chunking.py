# file: core/ai/rag/chunking.py
# purpose: 文本切片与清洗（简单分段 + 字数阈值聚合）
from __future__ import annotations
from typing import List


def chunk_text(text: str, *, max_chars: int = 1200, sep: str = "\n\n") -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in text.split(sep) if p.strip()]
    chunks: List[str] = []
    buf = ""
    for p in parts:
        if len(buf) + len(p) + len(sep) <= max_chars:
            buf = (buf + sep + p) if buf else p
        else:
            if buf:
                chunks.append(buf)
            if len(p) <= max_chars:
                buf = p
            else:
                # 过长段再切（按句号/全角句号）
                sents = [s for s in p.replace("。", ".").split(".") if s]
                cur = ""
                for s in sents:
                    s2 = s.strip() + "."
                    if len(cur) + len(s2) <= max_chars:
                        cur += s2
                    else:
                        if cur:
                            chunks.append(cur)
                        cur = s2
                if cur:
                    buf = cur
                else:
                    buf = ""
    if buf:
        chunks.append(buf)
    return chunks