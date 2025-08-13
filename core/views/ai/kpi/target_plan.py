# file: core/views/ai/kpi/target_plan.py
# purpose: 目标拟定接口：基于 baseline + 目标增幅生成按日拆分
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.kpi.targets import Period, make_targets
from core.ai.orchestrator import Orchestrator


class KpiTargetPlanView(View):
    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            period = Period.from_payload(payload.get("period") or {})
            lift_pct = float(payload.get("lift_pct", 10))
            baseline_mode = payload.get("baseline_mode", "last_period")  # last_period | yoy
            baseline_override = payload.get("baseline")  # 可选：[{date, sales}]

            plan = make_targets(
                tenant_id=tenant_id,
                period=period,
                goal_lift_pct=lift_pct,
                baseline_mode=baseline_mode,
                baseline_override=baseline_override,
            )

            # 可选：让 LLM 生成计划说明
            if bool(payload.get("with_commentary", False)):
                o = Orchestrator(tenant_id=tenant_id, agent="kpi")
                msg = (
                    "你是经营分析顾问，请用简洁中文说明该目标拆分的依据（历史 vs 目标增幅），并给出 2 条执行建议。\n"
                    f"计划: {plan}\n"
                )
                ans = o.chat_once(session=None, user_message=msg)
                plan.update({"commentary": ans.get("content"), "trace_id": ans.get("trace_id"), "tokens_spent": ans.get("spent")})

            return ok(plan)
        except ValueError as e:
            return fail(str(e), status=400)
        except Exception as e:
            return fail(str(e))