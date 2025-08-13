# file: core/views/ai/strategy/price.py
# purpose: 定价策略接口：POST /api/ai/strategy/price/ → 返回批量建议价；可选 LLM 文案说明
from __future__ import annotations
from typing import Any, Dict, List
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.strategy.price import suggest_prices, PriceBound
from core.ai.orchestrator import Orchestrator


class StrategyPriceView(View):
    """对传入的商品列表生成建议价格。
    请求：{"items":[{"product_id":1,"current_price"?:12.3,"cost"?:8.0}],"target_margin"?:0.3,"bounds"?:{pid:{min_price,max_price}},"with_explain"?:true}
    返回：{"items":[{product_id,current_price,suggested_price,reason}],"explain"?}
    """

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            items = list(payload.get("items") or [])
            target_margin = payload.get("target_margin")
            bounds_raw = payload.get("bounds") or {}
            with_explain = bool(payload.get("with_explain", False))

            # 解析 bounds
            bounds: Dict[Any, PriceBound] = {}
            for k, v in bounds_raw.items():
                try:
                    bounds[k] = PriceBound(min_price=v.get("min_price"), max_price=v.get("max_price"))
                except Exception:
                    pass

            sugs = suggest_prices(tenant_id=tenant_id, items=items, target_margin=target_margin, bounds=bounds)
            out: Dict[str, Any] = {"items": sugs}

            if with_explain:
                o = Orchestrator(tenant_id=tenant_id, agent="strategy-price")
                prompt = (
                    "你是定价策略专家。根据如下建议价列表，给出 3 条面向运营的中文建议，不要复述明细：\n" + str(sugs[:20])
                )
                ans = o.chat_once(session=None, user_message=prompt)
                out.update({"explain": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})
            return ok(out)
        except Exception as e:
            return fail(str(e))