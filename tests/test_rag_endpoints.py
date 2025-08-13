# file: tests/test_rag_endpoints.py
# purpose: RAG：入库+检索+生成流程基本打通
from __future__ import annotations
import json

def test_rag_ingest_and_query(db, client_with_tenant):
    # 1) 直接传文本入库
    payload = {"filename": "readme.txt", "content": "Alpha\n\nBeta gamma delta.\n\nOmega."}
    res = client_with_tenant.post("/api/ai/rag/ingest/", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200, res.content
    jid = res.json()["data"]["doc_id"]

    # 2) 基于文本检索+生成
    q = {"query": "gamma 是什么?", "top_k": 3}
    res2 = client_with_tenant.post("/api/ai/rag/query/", data=json.dumps(q), content_type="application/json")
    assert res2.status_code == 200, res2.content
    data = res2.json()["data"]
    assert "answer" in data and data["contexts"], data