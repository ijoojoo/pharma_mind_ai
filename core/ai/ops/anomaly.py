# file: core/views/ai/ops/anomaly.py
# purpose: 异常检测接口：接收 rules+window → 返回命中明细；可选 LLM 总结
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.ops.anomaly_rules import detect_anomalies
from core.ai.orchestrator import Orchestrator


_DEFAULT_RULES = [
    {"id": "r_sales_drop", "type": "sales_drop", "threshold_pct": 30, "lookback": 7, "group_by": ["store_id", "product_id"]},
    {"id": "r_stockout", "type": "stockout", "min_qty": 0, "group_by": ["store_id", "product_id"]},
]


class OpsAnomalyView(View):
    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            window = payload.get("window") or {}
            rules = payload.get("rules") or _DEFAULT_RULES
            with_commentary = bool(payload.get("with_commentary", False))

            items = detect_anomalies(tenant_id=tenant_id, window=window, rules=rules)
            out = {"items": items, "count": len(items)}

            if with_commentary:
                # 给出摘要与建议
                sample = items[:20]
                prompt = (
                    "你是运营分析专家。根据以下异常命中，输出：\n"
                    "1) 核心问题要点（不超过 3 条）\n"
                    "2) 可能原因假设（不超过 3 条）\n"
                    "3) 三条可执行动作建议（可落地）\n"
                    f"异常样本: {sample}\n"
                )
                o = Orchestrator(tenant_id=tenant_id, agent="ops")
                ans = o.chat_once(session=None, user_message=prompt)
                out.update({"summary": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})

            return ok(out)
        except Exception as e:
            return fail(str(e))
