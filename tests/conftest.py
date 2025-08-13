# file: tests/conftest.py
# purpose: 测试夹具：默认租户账户、禁用真实 LLM 调用、Django client headers
from __future__ import annotations
import pytest
from django.test import Client
from core.models.ai_billing import AiTenantTokenAccount


@pytest.fixture()
def tenant_id() -> str:
    return "t_demo"


@pytest.fixture()
def client_with_tenant(tenant_id) -> Client:
    c = Client(HTTP_X_TENANT_ID=tenant_id)
    return c


@pytest.fixture(autouse=True)
def _seed_token_account(db, tenant_id):
    AiTenantTokenAccount.objects.update_or_create(
        tenant_id=tenant_id,
        defaults={
            "plan": "pro",
            "token_balance": 1_000_000,
            "soft_limit": 1000,
            "hard_limit": 0,
            "status": "active",
        },
    )


@pytest.fixture(autouse=True)
def _mock_orchestrator(monkeypatch):
    """避免真实外呼，统一返回固定内容与花费。"""
    from core.ai.orchestrator import Orchestrator

    def _fake_chat_once(self, session, user_message: str):
        return {"content": f"OK: {user_message[:16]}", "spent": 123, "trace_id": "trace_test"}

    monkeypatch.setattr(Orchestrator, "chat_once", _fake_chat_once)
    yield