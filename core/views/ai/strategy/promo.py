# file: core/views/ai/strategy/promo.py
# purpose: 促销策略接口：POST /api/ai/strategy/promo/ → 返回候选与建议折扣；可选 LLM 文案
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.strategy.promo import suggest_promotions
from core.ai.orchestrator import Orchestrator


class StrategyPromoView(View):
    """返回促销候选 SKU。请求：{"top_k"?:20,"lookback"?:14,"with_explain"?:true}。"""

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            top_k = int(payload.get("top_k", 20))
            lookback = int(payload.get("lookback", 14))
            with_explain = bool(payload.get("with_explain", False))

            items = suggest_promotions(tenant_id=tenant_id, top_k=top_k, lookback=lookback)
            out = {"items": items, "count": len(items)}

            if with_explain:
                o = Orchestrator(tenant_id=tenant_id, agent="strategy-promo")
                prompt = (
                    "你是促销策划专家。请基于候选清单提供 3 条执行建议（时长/折扣/渠道），避免复述数据：\n" + str(items[:20])
                )
                ans = o.chat_once(session=None, user_message=prompt)
                out.update({"explain": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})
            return ok(out)
        except Exception as e:
            return fail(str(e))
