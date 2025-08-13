# file: core/ai/orchestrator.py
# purpose: 统一编排：模型解析（用户/租户/环境/回退） → 预授权 → 调用 Provider → 审计过滤 → 结算入库
from __future__ import annotations
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
import uuid
import time
import os

from django.db import transaction
from django.utils import timezone
from django.conf import settings

from core.ai.billing import ensure_can_consume, finalize_or_rollback
from core.ai.audit import apply_output_filters
from core.ai.llm.registry import create_provider, get_provider_meta, normalize_provider_key
from core.ai.llm.base import ProviderError, ProviderNotConfigured

# 日志模型（按你的项目模型命名）
from core.models.ai_logging import AiRun, AiCallLog, AiMessage

# 可选：用户/租户模型偏好解析（若不存在则回退 env/fallback）
try:
    from core.ai.model_prefs import get_effective_model  # 你之前的偏好解析实现
except Exception:  # 回退
    get_effective_model = None  # type: ignore


@dataclass
class OrchestratorConfig:
    provider_key: Optional[str] = None  # 显式指定；否则走 get_effective_model()
    model_name: Optional[str] = None
    temperature: float = 0.2
    timeout: int = 30


class Orchestrator:
    def __init__(self, *, tenant_id: str, agent: str = "general", config: Optional[OrchestratorConfig] = None):
        self.tenant_id = tenant_id
        self.agent = agent
        self.config = config or OrchestratorConfig()

    def chat_once(self, session: Optional[Any], user_message: str) -> Dict[str, Any]:
        trace_id = uuid.uuid4().hex
        started = time.time()

        # 1) 解析 Provider/Model
        prov_key, model_name, source = self._resolve_model(session=session)

        # 2) 预估 tokens 并做余额预授权
        est_in = self._estimate_in_tokens(user_message)
        ensure_can_consume(tenant_id=self.tenant_id, estimate_tokens=est_in, reason="llm_estimate")

        # 3) Provider 调用
        messages = self._build_messages(session=session, user_message=user_message)
        try:
            provider = create_provider(prov_key, timeout=self.config.timeout)
            result = provider.chat(messages=messages, model=model_name, stream=False, temperature=self.config.temperature)
            content = result.get("content", "")
            tokens_in = int(result.get("tokens_in") or est_in)
            tokens_out = int(result.get("tokens_out") or self._estimate_out_tokens(content))
            spent = tokens_in + tokens_out
        except (ProviderError, ProviderNotConfigured) as e:
            content = f"[provider_error] {e}"
            tokens_in = est_in
            tokens_out = 0
            spent = tokens_in

        # 4) 审计过滤（脱敏/医疗合规）
        filtered = apply_output_filters(tenant_id=self.tenant_id, text=content)
        content_final = filtered.get("text", content)

        # 5) 记录日志（Run/Call/Message）并结算
        latency_ms = int((time.time() - started) * 1000)
        with transaction.atomic():
            run = AiRun.objects.create(
                trace_id=trace_id,
                tenant_id=self.tenant_id,
                agent=self.agent,
                session=session,
                latency_ms=latency_ms,
                created_at=timezone.now(),
            )
            AiCallLog.objects.create(
                run=run,
                provider=prov_key,
                model=model_name or get_provider_meta(prov_key).default_model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
            )
            AiMessage.objects.create(
                session=session,
                role="user",
                content=user_message,
                tokens_in=tokens_in,
            )
            AiMessage.objects.create(
                session=session,
                role="assistant",
                content=content_final,
                tokens_out=tokens_out,
            )
        finalize_or_rollback(tenant_id=self.tenant_id, run_id=trace_id, actual_tokens=spent, success=True, reason="llm_usage")

        return {"content": content_final, "spent": spent, "trace_id": trace_id}

    # -- internals ------------------------------------------------------------
    def _env_provider(self) -> Optional[str]:
        """从 Django settings 或环境变量读取默认 Provider；均缺失则返回 None。"""
        val = getattr(settings, "LLM_PROVIDER", None)
        if not val:
            val = os.getenv("LLM_PROVIDER")
        return val

    def _resolve_model(self, session: Optional[Any]):
        # 优先：构造器参数 → 用户偏好 → 环境/回退（mock）
        key = normalize_provider_key(self.config.provider_key) if self.config.provider_key else None
        model = self.config.model_name
        source = "config"
        if not key and get_effective_model:
            try:
                em = get_effective_model(
                    tenant_id=self.tenant_id,
                    user_id=getattr(session, "user_id", None),
                    env_provider=self._env_provider(),
                    fallback_provider="mock",
                )
                key, model, source = em.provider, em.model_name, em.source
            except Exception:
                pass
        if not key:
            key = normalize_provider_key(self._env_provider()) or "mock"
            source = "env" if key != "mock" else "fallback"
        if not model:
            model = get_provider_meta(key).default_model
        return key, model, source

    def _build_messages(self, session: Optional[Any], user_message: str) -> List[Dict[str, str]]:
        sys_prompt = "你是 PharmaMindAI 的专业助手，回答要简洁、准确。"
        return [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message},
        ]

    def _estimate_in_tokens(self, text: str) -> int:
        try:
            from core.ai.llm.providers.mock import MockProvider
            return MockProvider.estimate_tokens(text)
        except Exception:
            return max(1, len(text) // 4)

    def _estimate_out_tokens(self, text: str) -> int:
        return self._estimate_in_tokens(text)