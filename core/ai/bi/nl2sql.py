# file: core/ai/bi/nl2sql.py
# purpose: 自然语言到受控查询的生成器
# - 不信任 LLM 直接写 SQL；只让其输出结构化意图（view、聚合列、维度、筛选等）
# - 再由本模块根据白名单字段拼接安全 SQL
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from core.ai.bi.schema import ALLOWED_VIEWS, VIEW_COLUMNS


@dataclass
class QueryIntent:
    """描述一次受控的 BI 查询意图。"""
    view_key: str                 # 视图别名（如 'sales'）
    dimensions: List[str]         # 维度列（必须在白名单）
    metrics: List[str]            # 指标列（必须在白名单）
    filters: Dict[str, Any]       # 简单等值/范围条件
    order_by: List[str]           # 排序列（带可选 "-" 号表示倒序）
    limit: int = 500              # 限制行数

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _resolve_view(view_key: str) -> str:
    if view_key not in ALLOWED_VIEWS:
        raise ValueError(f"unknown view_key: {view_key}")
    return ALLOWED_VIEWS[view_key]


def _validate_cols(view_name: str, cols: List[str]) -> List[str]:
    allowed = set(VIEW_COLUMNS.get(view_name, []))
    out: List[str] = []
    for c in cols or []:
        name = str(c).lstrip("+")  # 兼容前端传如 +amount
        name = name.lstrip("-")
        if name not in allowed:
            raise ValueError(f"invalid column '{name}' for view '{view_name}'")
        out.append(c)
    return out


def build_sql(intent: QueryIntent) -> str:
    """根据意图拼接 SQL。仅允许 SELECT 指定列 + FROM 白名单视图 + WHERE 简单条件 + GROUP BY + ORDER BY + LIMIT。"""
    view = _resolve_view(intent.view_key)
    dims = _validate_cols(view, intent.dimensions)
    mets = _validate_cols(view, intent.metrics)
    all_cols = dims + mets if dims or mets else [VIEW_COLUMNS[view][0]]
    select_list = ", ".join(all_cols)

    # WHERE（仅支持等号与范围）
    where_parts: List[str] = []
    for k, v in (intent.filters or {}).items():
        if k not in VIEW_COLUMNS.get(view, []):
            raise ValueError(f"invalid filter column '{k}'")
        if isinstance(v, dict):
            if "gte" in v:
                where_parts.append(f"{k} >= %({k}__gte)s")
            if "lte" in v:
                where_parts.append(f"{k} <= %({k}__lte)s")
        else:
            where_parts.append(f"{k} = %({k})s")
    where_sql = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

    # GROUP BY：仅当存在维度 + 指标时启用
    group_sql = f" GROUP BY {', '.join(dims)}" if dims and mets else ""

    # ORDER BY：校验列并处理升降序
    order_items: List[str] = []
    for ob in intent.order_by or []:
        desc = ob.startswith("-")
        name = ob[1:] if desc else ob
        if name not in VIEW_COLUMNS.get(view, []):
            raise ValueError(f"invalid order_by '{name}'")
        order_items.append(f"{name} {'DESC' if desc else 'ASC'}")
    order_sql = f" ORDER BY {', '.join(order_items)}" if order_items else ""

    limit = max(1, min(int(intent.limit or 500), 5000))

    return f"SELECT {select_list} FROM {view}{where_sql}{group_sql}{order_sql}"