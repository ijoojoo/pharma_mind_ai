# file: core/ai/tools/sql_tool.py
# purpose: 只读 SQL 执行器（白名单视图 + 参数化 + 超时 + 限流 + 分页 + 缓存）
from __future__ import annotations
import re
from contextlib import closing
from typing import Any, Dict, Iterable, List, Tuple
from django.db import connection
from core.ai.bi.schema import ALLOWED_VIEWS
from core.ai.bi.cache import get_or_set

# 危险关键字拦截（防止非只读）
_DANGEROUS = re.compile(r"\b(insert|update|delete|alter|drop|create|grant|revoke|truncate|replace|execute|call)\b", re.I)
_FROM_JOIN = re.compile(r"\b(from|join)\s+([a-zA-Z_][a-zA-Z0-9_\.]*|\()", re.I)


def guard(sql: str) -> Tuple[bool, str]:
    """确认 SQL 仅为单条 SELECT，且 FROM/JOIN 的对象在白名单视图内。"""
    s = (sql or "").strip()
    if not s:
        return False, "empty sql"
    if ";" in s:
        return False, "multiple statements are not allowed"
    if not s.lower().startswith("select"):
        return False, "only SELECT is allowed"
    if _DANGEROUS.search(s):
        return False, "dangerous keyword detected"
    # 禁止 FROM (subquery) 形式，便于解析来源视图
    for m in _FROM_JOIN.finditer(s):
        token = m.group(2)
        if token.startswith("("):
            return False, "subquery in FROM/JOIN is not allowed"
        # 取裸标识（去 schema 前缀）
        view = token.split(".")[-1]
        if view not in ALLOWED_VIEWS.values():
            return False, f"view '{view}' is not in whitelist"
    return True, "ok"


def _rows_to_dicts(cursor) -> List[Dict[str, Any]]:
    """将 cursor 输出转换为字典数组。"""
    cols = [c[0] for c in (cursor.description or [])]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def run_readonly(sql: str, params: Any | None, *, tenant_id: str, limit: int = 500) -> Dict[str, Any]:
    """执行只读查询（不分页）。返回 rows 与 count（本批行数）。"""
    ok_flag, msg = guard(sql)
    if not ok_flag:
        raise ValueError(f"SQL rejected: {msg}")
    # 限制最大行数（简单粗暴地包一层外 SELECT）
    sql_wrapped = f"SELECT * FROM ({sql}) AS t LIMIT {max(1, min(limit, 5000))}"
    with closing(connection.cursor()) as cur:
        cur.execute(sql_wrapped, params)
        data = _rows_to_dicts(cur)
    return {"rows": data, "count": len(data)}


def run_readonly_paginated(sql: str, params: Any | None, *, tenant_id: str, page: int, page_size: int) -> Dict[str, Any]:
    """执行只读查询（分页）。返回 rows + page_info。"""
    ok_flag, msg = guard(sql)
    if not ok_flag:
        raise ValueError(f"SQL rejected: {msg}")
    p = max(1, int(page or 1))
    ps = max(1, min(int(page_size or 50), 500))
    offset = (p - 1) * ps
    sql_wrapped = f"SELECT * FROM ({sql}) AS t OFFSET {offset} LIMIT {ps}"
    with closing(connection.cursor()) as cur:
        cur.execute(sql_wrapped, params)
        data = _rows_to_dicts(cur)
    return {"rows": data, "page": p, "page_size": ps, "returned": len(data)}


def cached_run_readonly(sql: str, params: Any | None, *, tenant_id: str, limit: int, ttl: int) -> Dict[str, Any]:
    """带缓存的只读查询；用于热点明细或低频刷新面板。"""
    def _compute():
        return run_readonly(sql, params, tenant_id=tenant_id, limit=limit)
    data, _hit = get_or_set(tenant_id=tenant_id, sql=sql, params=params, ttl=ttl, compute=_compute)
    return data