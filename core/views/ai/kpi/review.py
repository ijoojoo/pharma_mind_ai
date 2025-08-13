# file: core/views/ai/kpi/review.py
# purpose: 复盘接口：对比实际 vs 目标，返回差额/状态 + 可选 LLM 总结
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.kpi.targets import Period
from core.ai.kpi.review import review
from core.ai.orchestrator import Orchestrator


class KpiReviewView(View):
    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            period = Period.from_payload(payload.get("period") or {})
            targets_daily = payload.get("targets_daily")  # 必需：[{date, target}]
            if not targets_daily:
                return fail("Missing targets_daily", status=400)
            actuals = payload.get("actuals")  # 可选：[{date, sales}]；为空则从库汇总
            tol = float(payload.get("tolerance", 0.05))

            res = review(tenant_id=tenant_id, period=period, targets_daily=targets_daily, actuals_override=actuals, tolerance=tol)
            out = {
                "total_actual": res.total_actual,
                "total_target": res.total_target,
                "gap": res.gap,
                "gap_pct": res.gap_pct,
                "on_track": res.on_track,
                "daily": res.daily,
            }

            if bool(payload.get("with_commentary", False)):
                o = Orchestrator(tenant_id=tenant_id, agent="kpi")
                msg = (
                    "请用中文总结复盘结论：\n"
                    "- 是否在轨（原因）\n- 2 条纠偏建议（短期/中期）\n"
                    f"数据: {out}\n"
                )
                ans = o.chat_once(session=None, user_message=msg)
                out.update({"summary": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})

            return ok(out)
        except ValueError as e:
            return fail(str(e), status=400)
        except Exception as e:
            return fail(str(e))
