# file: core/views/ai/bi/nlp_query.py
# purpose: 自然语言到 SQL 的安全查询接口（POST /api/ai/bi/query/）
# - 输入：{question, view_key, filters?, order_by?, limit?, with_commentary?}
# - 过程：调用 LLM 仅生成结构化意图 → 本地拼接安全 SQL → 执行 → 返回 rows 与可选解读
from __future__ import annotations
from typing import Any, Dict
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.orchestrator import Orchestrator
from core.ai.bi.schema import HELP_TEXT
from core.ai.bi.nl2sql import QueryIntent, build_sql
from core.ai.tools.sql_tool import run_readonly


class BiNlpQueryView(View):
    """自然语言问答到受控 SQL 的入口。"""

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            question = (payload.get("question") or "").strip()
            view_key = (payload.get("view_key") or "sales").strip()  # 默认查询销量视图
            if not question:
                return fail("Missing question", status=400)
            filters = payload.get("filters") or {}
            order_by = payload.get("order_by") or []
            limit = int(payload.get("limit", 200))
            with_commentary = bool(payload.get("with_commentary", False))

            # 1) 让 LLM 输出结构化意图（不直接写 SQL）
            o = Orchestrator(tenant_id=tenant_id, agent="bi-nl2sql")
            sys_help = HELP_TEXT.get(view_key, "")
            ask = (
                "根据业务问题，给出一个受控查询意图 JSON，字段包含：\n"
                "- dimensions: 维度列数组（可为空）\n- metrics: 指标列数组（可为空）\n"
                "- filters: 过滤条件对象（等值或范围，如 {category:'OTC', biz_date:{gte:'2025-08-01', lte:'2025-08-07'}}）\n"
                "- order_by: 排序（列名数组，'-'前缀表示降序）\n"
                f"已知视图字段：{sys_help}\n"
                f"业务问题：{question}\n"
                "请仅输出 JSON，不要多余文字。"
            )
            resp = o.chat_once(session=None, user_message=ask)
            raw = resp.get("content") or "{}"
            try:
                import json
                intent_obj = json.loads(raw)
            except Exception:
                # 回退：简单猜测
                intent_obj = {"dimensions": ["biz_date"], "metrics": ["amount"], "filters": {}, "order_by": ["-biz_date"]}

            # 2) 拼装受控 SQL
            qi = QueryIntent(
                view_key=view_key,
                dimensions=list(intent_obj.get("dimensions") or []),
                metrics=list(intent_obj.get("metrics") or []),
                filters=dict(intent_obj.get("filters") or {}),
                order_by=list(order_by or intent_obj.get("order_by") or []),
                limit=limit,
            )
            sql = build_sql(qi)

            # 3) 将 filters 转为 DB 参数
            params: Dict[str, Any] = {}
            for k, v in (qi.filters or {}).items():
                if isinstance(v, dict):
                    if "gte" in v:
                        params[f"{k}__gte"] = v["gte"]
                    if "lte" in v:
                        params[f"{k}__lte"] = v["lte"]
                else:
                    params[k] = v

            # 4) 执行并返回
            result = run_readonly(sql, params, tenant_id=tenant_id, limit=limit)
            out = {"rows": result["rows"], "count": result["count"], "sql": sql}

            if with_commentary:
                msg = (
                    "你是 BI 分析师。用简洁中文总结 2-3 条洞察，不要复述 SQL，也不要虚构不存在的字段。数据预览：" + str(result["rows"][:20])
                )
                ans = o.chat_once(session=None, user_message=msg)
                out.update({"llm_commentary": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})

            return ok(out)
        except ValueError as e:
            return fail(str(e), status=400)
        except Exception as e:
            return fail(str(e))
