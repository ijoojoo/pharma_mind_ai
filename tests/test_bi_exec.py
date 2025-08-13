# file: tests/test_bi_exec.py
# purpose: BI：只读 SQL 执行器（白名单 + 真实执行到 django_migrations）
from __future__ import annotations
import json
from core.ai.bi import schema as bi_schema


def test_bi_exec_readonly(db, client_with_tenant, monkeypatch):
    monkeypatch.setattr(bi_schema, "ALLOWED_VIEWS", {"migrations": "django_migrations"})
    sql = "SELECT app, name FROM django_migrations"
    res = client_with_tenant.post("/api/ai/bi/exec/", data=json.dumps({"sql": sql, "limit": 5}), content_type="application/json")
    assert res.status_code == 200, res.content
    out = res.json()["data"]
    assert out["count"] >= 0
    assert isinstance(out["rows"], list)
