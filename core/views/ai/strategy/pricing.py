# file: core/views/ai/strategy/pricing.py
# purpose: 定价接口：返回建议价格 + 可选 LLM 解释（通过 Orchestrator）
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.strategy.pricing import suggest_price
from core.ai.orchestrator import Orchestrator


class StrategyPricingView(View):
    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            product = payload.get("product") or {}
            constraints = payload.get("constraints") or {}
            with_commentary = bool(payload.get("with_commentary", False))

            res = suggest_price(product, constraints)
            out = {"suggest": res}

            if with_commentary:
                o = Orchestrator(tenant_id=tenant_id, agent="strategy")
                explain_prompt = (
                    "你是零售定价专家。请用简洁中文解释以下定价建议，列出：\n"
                    "1) 该价格如何满足毛利/竞品约束 \n"
                    "2) 可能的风险与监控指标 \n"
                    f"定价数据: {res}\n"
                )
                ans = o.chat_once(session=None, user_message=explain_prompt)
                out.update({"commentary": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})

            return ok(out)
        except Exception as e:
            return fail(str(e))
