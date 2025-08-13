# file: core/views/ai/system/billing.py
# purpose: 系统-计费视图：余额查询与充值；兼容旧服务接口命名
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.billing import (
    get_or_create_account,
    get_balance,
    topup_tokens,
)


class TokenBalanceView(View):
    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            data = get_balance(tenant_id=tenant_id)
            return ok(data)
        except Exception as e:
            return fail(str(e))


class TokenTopupView(View):
    def post(self, request: HttpRequest):
        try:
            payload = get_json(request)
            tenant_id = request.headers.get("X-Tenant-Id") or payload.get("tenant_id")
            if not tenant_id:
                return fail("Missing tenant_id", status=400)
            tokens = int(payload.get("tokens", 0))
            reason = str(payload.get("reason") or "manual_topup")
            if tokens <= 0:
                return fail("tokens must be > 0", status=400)
            out = topup_tokens(tenant_id=tenant_id, tokens=tokens, reason=reason)
            return ok(out)
        except ValueError as e:
            return fail(str(e), status=400)
        except Exception as e:
            return fail(str(e))
