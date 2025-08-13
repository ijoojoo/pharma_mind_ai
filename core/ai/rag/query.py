# file: core/views/ai/rag/query.py
# purpose: RAG 检索/生成接口：POST {query, top_k, with_answer}；可调用 Orchestrator 生成最终答案
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.rag.search import search_chunks, build_context
from core.ai.orchestrator import Orchestrator


class RagQueryView(View):
    """执行检索，返回匹配片段；with_answer=true 时，用检索上下文+问题调用 LLM 生成答案。"""

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            query = (payload.get("query") or "").strip()
            if not query:
                return fail("Missing query", status=400)
            top_k = int(payload.get("top_k", 5))
            with_answer = bool(payload.get("with_answer", False))

            hits = search_chunks(tenant_id=tenant_id, query=query, top_k=top_k)
            out = {"hits": hits, "count": len(hits)}

            if with_answer:
                ctx = build_context(hits)
                if ctx:
                    prompt = (
                        "你将基于检索到的资料回答问题。若资料不足以回答，请明确说明‘依据不足’。\n"  # 合规与防幻觉
                        "资料如下：\n" + ctx + "\n\n问题：" + query
                    )
                    ans = Orchestrator(tenant_id=tenant_id, agent="rag").chat_once(session=None, user_message=prompt)
                    out.update({"answer": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})
            return ok(out)
        except Exception as e:
            return fail(str(e))