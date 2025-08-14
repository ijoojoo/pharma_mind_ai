# file: core/ai/llm/providers/base.py
# purpose: LLM 适配器基类与标准返回结构；子类仅需实现 `_chat_impl()` 完成实际 HTTP 调用。

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


def _estimate_tokens(text: str) -> int:
    """基于字符长度粗估 Token 数（中英混合按 ~2.2 字/token 估算）。
    用途：供应商未返回 usage 时用于计费回退，避免漏记。"""
    if not text:
        return 0
    return max(1, int(len(text) / 2.2))


@dataclass
class ChatResult:
    """标准聊天返回结构，Orchestrator 据此记账与回传。"""
    content: str            # 模型生成的文本内容
    tokens_in: int          # 输入 token 数
    tokens_out: int         # 输出 token 数
    raw: Dict[str, Any]     # 供应商原始响应（保留以便审计/排障）


class BaseAdapter:
    """LLM 适配器基类：提供统一的 `chat()` 接口与耗时统计/usage 回退估算。"""

    provider: str = "base"     # 供应商标识（例如 gemini/deepseek/zhipu）
    default_model: str = ""     # 默认模型名（子类覆盖）

    def __init__(self, *, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 30.0):
        """初始化适配器实例。
        :param api_key: 供应商 API Key（可从环境变量读取）
        :param model: 模型名称；为空则使用 default_model
        :param timeout: HTTP 超时时间（秒）
        """
        self.api_key = api_key
        self.model = model or self.default_model
        self.timeout = timeout

    def chat(self, prompt: str) -> ChatResult:
        """单轮对话统一入口：调用 `_chat_impl()`，并做 usage 回退估算与耗时统计。"""
        t0 = time.perf_counter()
        data = self._chat_impl(prompt)
        content = data.get("content") or ""
        # usage 回退估算，避免供应商未返回 tokens 时无法扣费
        ti = int(data.get("tokens_in") or 0) or _estimate_tokens(prompt)
        to = int(data.get("tokens_out") or 0) or _estimate_tokens(content)
        data.setdefault("latency_ms", int((time.perf_counter() - t0) * 1000))
        return ChatResult(content=content, tokens_in=ti, tokens_out=to, raw=data)

    def _chat_impl(self, prompt: str) -> Dict[str, Any]:  # pragma: no cover
        """子类实现：实际 HTTP 调用并返回字典 {content, tokens_in?, tokens_out?, raw}。"""
        raise NotImplementedError
