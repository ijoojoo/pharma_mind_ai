# file: tests/test_billing.py
# purpose: 计费：充值与扣费流程
from __future__ import annotations
from core.ai.billing import topup, finalize_or_rollback
from core.models.ai_billing import AiTenantTokenAccount


def test_topup_and_finalize(db, tenant_id):
    acc = AiTenantTokenAccount.objects.get(tenant_id=tenant_id)
    bal0 = int(acc.token_balance)
    r1 = topup(tenant_id=tenant_id, tokens=500)
    assert r1["added"] == 500
    acc.refresh_from_db()
    assert int(acc.token_balance) == bal0 + 500

    r2 = finalize_or_rollback(tenant_id=tenant_id, run_id="run_x", actual_tokens=200, success=True)
    assert r2["deducted"] == 200
    acc.refresh_from_db()
    assert int(acc.token_balance) == bal0 + 300
