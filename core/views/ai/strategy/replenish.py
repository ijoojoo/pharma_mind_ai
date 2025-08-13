# file: core/views/ai/strategy/replenish.py
# purpose: 补货策略接口：POST /api/ai/strategy/replenish/ → 返回安全库存/再订货点/建议订货量
from __future__ import annotations
from typing import Any, List
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.strategy.replenish import suggest_replenishment
from core.ai.orchestrator import Orchestrator


class StrategyReplenishView(View):
    """请求：{"product_ids":[...],"lookback_days"?:28,"leadtime_days"?:7,"service_level"?:0.95,"with_explain"?:true}。"""

    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            product_ids: List[Any] = list(payload.get("product_ids") or [])
            if not product_ids:
                return fail("Missing product_ids", status=400)
            lookback_days = int(payload.get("lookback_days", 28))
            leadtime_days = float(payload.get("leadtime_days", 7.0))
            service_level = float(payload.get("service_level", 0.95))
            with_explain = bool(payload.get("with_explain", False))

            items = suggest_replenishment(tenant_id=tenant_id, product_ids=product_ids, lookback_days=lookback_days,
                                          leadtime_days=leadtime_days, service_level=service_level)
            out = {"items": items, "count": len(items)}

            if with_explain:
                o = Orchestrator(tenant_id=tenant_id, agent="strategy-replenish")
                prompt = (
                    "你是库存补货专家。请基于以下结果，给门店/仓库提供 3 条落地建议（频率/批量/阈值），避免复述数据：\n" + str(items[:20])
                )
                ans = o.chat_once(session=None, user_message=prompt)
                out.update({"explain": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})
            return ok(out)
        except Exception as e:
            return fail(str(e))