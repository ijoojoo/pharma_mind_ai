# file: core/views/ai/ops/daily_insight.py
# purpose: 运营日结：计算基础指标 + 调用 LLM 生成洞察（触发计费与留痕）
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.ops.daily_insight import compute_daily_metrics
from core.ai.orchestrator import Orchestrator


class OpsDailyInsightView(View):
    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            store_ids = payload.get("store_ids") or []
            metrics = compute_daily_metrics(store_ids=store_ids)
            # 调 LLM 输出洞察
            prompt = (
                "请基于以下指标给出 3 条可执行的运营洞察，并建议一张合适的可视化图表类型。\n" \
                f"指标: {metrics}\n"
            )
            o = Orchestrator(tenant_id=tenant_id, agent="ops")
            ans = o.chat_once(session=None, user_message=prompt)
            return ok({"metrics": metrics, "insight": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})
        except Exception as e:
            return fail(str(e))


