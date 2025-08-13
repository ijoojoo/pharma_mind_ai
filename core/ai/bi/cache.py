# file: core/ai/bi/cache.py
# purpose: 只读查询的简易缓存（Django cache），用于降低热点查询压力
from __future__ import annotations
import hashlib
import json
from typing import Any, Dict, Tuple
from django.core.cache import cache


def _key_for(tenant_id: str, sql: str, params: Any) -> str:
    payload = json.dumps({"t": tenant_id, "sql": sql, "p": params}, sort_keys=True, ensure_ascii=False)
    return "bi:ro:" + hashlib.md5(payload.encode("utf-8")).hexdigest()


def get_or_set(*, tenant_id: str, sql: str, params: Any, ttl: int, compute) -> Tuple[dict, bool]:
    key = _key_for(tenant_id, sql, params)
    val = cache.get(key)
    if val is not None:
        return val, True
    data = compute()
    cache.set(key, data, timeout=max(1, int(ttl)))
    return data, False
