# file: core/openapi/ai_schema.py
# purpose: 生成 AI 模块的 OpenAPI 3.0 Schema（纯 Python 构造，不依赖 DRF/三方库）；
#          供视图 /api/ai/system/openapi.json 输出给 Swagger UI/Redoc 使用。
from __future__ import annotations
from typing import Any, Dict

API_TITLE = "PharmaMindAI · AI API"
API_VERSION = "1.0.0"


def _ok_schema(example: Any = None) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "data": {"nullable": True},
        },
        "example": {"success": True, "data": example or {"ok": True}},
    }


def _err_schema(code: str = "bad_request") -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "example": code},
                    "message": {"type": "string", "example": "错误说明"},
                },
            },
        },
    }


def build_schema(server_url: str | None = None) -> Dict[str, Any]:
    """构造最重要端点的 OpenAPI JSON（覆盖 system/bi/ops/strategy）。"""
    servers = [{"url": server_url}] if server_url else []
    return {
        "openapi": "3.0.3",
        "info": {"title": API_TITLE, "version": API_VERSION},
        "servers": servers,
        "paths": {
            "/api/ai/system/health/": {
                "get": {
                    "summary": "系统健康检查",
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": _ok_schema({"ok": True, "items": []})}}}},
                }
            },
            "/api/ai/system/selfcheck/": {
                "get": {
                    "summary": "租户自检（需 X-Tenant-Id）",
                    "parameters": [{"in": "header", "name": "X-Tenant-Id", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": _ok_schema({"ok": True, "items": []})}}},
                                   "400": {"description": "Missing tenant", "content": {"application/json": {"schema": _err_schema("bad_request")}}}},
                }
            },
            "/api/ai/system/usage/summary/": {
                "get": {
                    "summary": "用量汇总",
                    "parameters": [
                        {"in": "header", "name": "X-Tenant-Id", "required": True, "schema": {"type": "string"}},
                        {"in": "query", "name": "from", "schema": {"type": "string", "format": "date"}},
                        {"in": "query", "name": "to", "schema": {"type": "string", "format": "date"}},
                    ],
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": _ok_schema({"tenant_id": "demo"})}}}},
                }
            },
            "/api/ai/system/usage/runs/": {
                "get": {
                    "summary": "最近调用列表",
                    "parameters": [
                        {"in": "header", "name": "X-Tenant-Id", "required": True, "schema": {"type": "string"}},
                        {"in": "query", "name": "limit", "schema": {"type": "integer", "default": 20}},
                    ],
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": _ok_schema({"items": []})}}}},
                }
            },
            "/api/ai/bi/query/": {
                "post": {
                    "summary": "自然语言→SQL（白名单视图）",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {"question": {"type": "string"}, "view_key": {"type": "string"}, "limit": {"type": "integer"}}}}}},
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": _ok_schema({"sql": "SELECT ...", "rows": []})}}},
                                   "400": {"description": "Rejected", "content": {"application/json": {"schema": _err_schema("ai.sql.rejected")}}}},
                }
            },
            "/api/ai/bi/exec/": {
                "post": {
                    "summary": "执行只读 SQL（白名单视图）",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {"sql": {"type": "string"}, "params": {"type": "object"}, "limit": {"type": "integer"}}}}}},
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": _ok_schema({"rows": [], "chart_spec": {}})}}},
                                   "400": {"description": "Rejected", "content": {"application/json": {"schema": _err_schema("ai.sql.rejected")}}}},
                }
            },
            "/api/ai/ops/scan/": {
                "post": {
                    "summary": "触发一次异常扫描",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {"window": {"type": "object"}, "notify": {"type": "boolean"}}}}}},
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": _ok_schema({"items": []})}}}},
                }
            },
            "/api/ai/ops/rules/": {
                "get": {"summary": "列出规则", "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": _ok_schema({"items": []})}}}}},
                "post": {"summary": "创建规则", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}},
                          "responses": {"200": {"description": "Created", "content": {"application/json": {"schema": _ok_schema({"id": 1})}}}}},
            },
            "/api/ai/ops/rules/{rid}/": {
                "patch": {"summary": "更新规则", "parameters": [{"in": "path", "name": "rid", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
                "delete": {"summary": "删除规则", "parameters": [{"in": "path", "name": "rid", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
            },
            "/api/ai/ops/channels/": {
                "get": {"summary": "列出通道", "responses": {"200": {"description": "OK"}}},
                "post": {"summary": "创建通道", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}}, "responses": {"200": {"description": "OK"}}},
            },
            "/api/ai/ops/channels/{cid}/": {
                "patch": {"summary": "更新通道", "parameters": [{"in": "path", "name": "cid", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
                "delete": {"summary": "删除通道", "parameters": [{"in": "path", "name": "cid", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
            },
            "/api/ai/ops/channels/{cid}/test/": {
                "post": {"summary": "测试通道发送", "parameters": [{"in": "path", "name": "cid", "required": True, "schema": {"type": "string"}}], "responses": {"200": {"description": "OK"}}},
            },
            "/api/ai/ops/incidents/": {
                "get": {"summary": "事件列表", "responses": {"200": {"description": "OK"}}},
            },
            "/api/ai/ops/incidents/{iid}/{action}/": {
                "post": {"summary": "事件操作（ack/close/reopen）", "parameters": [
                    {"in": "path", "name": "iid", "required": True, "schema": {"type": "string"}},
                    {"in": "path", "name": "action", "required": True, "schema": {"type": "string"}},], "responses": {"200": {"description": "OK"}}},
            },
            "/api/ai/strategy/price/": {
                "post": {"summary": "定价建议", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}}, "responses": {"200": {"description": "OK"}}},
            },
            "/api/ai/strategy/promo/": {
                "post": {"summary": "促销候选", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}}, "responses": {"200": {"description": "OK"}}},
            },
            "/api/ai/strategy/replenish/": {
                "post": {"summary": "补货建议", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}}, "responses": {"200": {"description": "OK"}}},
            },
        },
        "components": {
            "securitySchemes": {},
        },
    }