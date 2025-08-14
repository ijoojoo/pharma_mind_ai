# file: core/ai/orchestrator.py
# purpose: 统一多供应商调度器（更新版）：加入 GPTAdapter 与 MockAdapter；选择模型 → 预授权 → 调用 → 审计 → 结算
# 兼容现有调用：chat_once(session, user_message) → {content, trace_id, spent, provider, model}

from __future__ import annotations
import os
import uuid
import time
from typing import Dict, Any, Optional

from core.ai.llm.providers import (
    GPTAdapter,
    MockAdapter,
    GeminiAdapter,
    DeepSeekAdapter,
    ZhipuAdapter,
)
from core.ai.model_prefs import get_effective_model  # 解析用户/租户/环境的有效模型
from core.ai.audit import apply_output_filters  # 输出脱敏与宣称审计
from core.ai.billing import begin_authorize, finalize_or_rollback  # 预授权/结算
from core.utils.rate_limit import rate_limiter


_ADAPTERS = {
    "gpt": GPTAdapter,
    "mock": MockAdapter,
    "gemini": GeminiAdapter,
    "deepseek": DeepSeekAdapter,
    "zhipu": ZhipuAdapter,
}


class Orchestrator:
    """多供应商调度器：一次完整 AI 请求生命周期的编排。"""

    def __init__(self, *, tenant_id: str, user_id: Optional[str] = None, agent: str = "chat"):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.agent = agent

    def _pick_adapter(self, provider_key: str, model_name: Optional[str]):
        """根据 provider_key 选择适配器类并实例化；若未知提供商则抛出 KeyError。"""
        cls = _ADAPTERS.get(provider_key)
        if not cls:
            raise KeyError(provider_key)
        return cls(model=model_name)

    def chat_once(self, *, session: Optional[str], user_message: str) -> Dict[str, Any]:
        """单轮对话：限流 → 选型 → 预授权 → 请求 → 审计 → 结算 → 返回。"""
        if not rate_limiter.is_allowed(self.tenant_id, cost=1.0):
            raise RuntimeError("rate limited")

        env_provider = os.getenv("LLM_PROVIDER")
        em = get_effective_model(tenant_id=self.tenant_id, user_id=self.user_id, env_provider=env_provider, fallback_provider="mock")
        provider_key, model_name = em.provider, em.model_name

        adapter = self._pick_adapter(provider_key, model_name)

        estimate = max(32, len(user_message) // 2)
        auth = begin_authorize(tenant_id=self.tenant_id, estimate_tokens=estimate)
        if not auth.allowed:
            return {"content": f"余额不足：{auth.reason}", "spent": 0, "trace_id": uuid.uuid4().hex}

        trace_id = uuid.uuid4().hex
        t0 = time.perf_counter()
        ok = False
        tokens_in = tokens_out = 0
        content = ""
        raw: Dict[str, Any] = {}
        try:
            res = adapter.chat(user_message)
            tokens_in, tokens_out = res.tokens_in, res.tokens_out
            filt = apply_output_filters(tenant_id=self.tenant_id, text=res.content)
            content = filt.get("text") or res.content
            raw = res.raw
            ok = True
            return {
                "content": content,
                "trace_id": trace_id,
                "spent": int(tokens_in + tokens_out),
                "provider": provider_key,
                "model": model_name,
                "latency_ms": int((time.perf_counter() - t0) * 1000),
            }
        finally:
            try:
                finalize_or_rollback(
                    tenant_id=self.tenant_id,
                    run_id=trace_id,
                    actual_tokens=int(tokens_in + tokens_out),
                    success=ok,
                    reason=f"llm_{provider_key}",
                )
            except Exception:
                pass
