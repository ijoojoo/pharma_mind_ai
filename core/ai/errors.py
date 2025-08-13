# file: core/ai/errors.py
# purpose: 统一错误码与说明；视图层可复用 code 常量，统一前端处理与文档展示
from __future__ import annotations
from typing import Dict

# 约定：命名以域前缀区分，便于定位
ERRORS: Dict[str, str] = {
    # 通用
    "bad_request": "请求参数错误",
    "unauthorized": "未授权或会话失效",
    "forbidden": "无权限执行该操作",
    "not_found": "资源不存在",
    "rate_limited": "请求过于频繁，稍后再试",
    "server_error": "服务器内部错误",

    # AI 计费
    "ai.account_suspended": "AI 账户已停用",
    "ai.insufficient_balance": "AI 令牌余额不足",

    # AI BI/SQL
    "ai.sql.rejected": "SQL 不被允许（仅白名单视图、禁止子查询/DML）",

    # AI OPS
    "ai.ops.rule_missing": "规则不存在或已禁用",

    # AI Strategy
    "ai.strategy.param_invalid": "策略参数不合法",
}


def list_error_codes() -> Dict[str, str]:
    """返回所有错误码→中文说明映射（用于文档/前端渲染）。"""
    return dict(ERRORS)