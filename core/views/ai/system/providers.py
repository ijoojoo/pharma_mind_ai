# file: core/views/ai/system/providers.py
# purpose: LLM 供应商偏好设置接口：支持 user/tenant 两级；写入 model_prefs。

from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json
from core.ai.model_prefs import set_user_model, set_tenant_default_model


class SetProviderView(View):
    """POST /api/ai/system/provider/set/ 设置用户或租户级默认供应商与模型。
    请求体: {scope: "user"|"tenant", provider: "gemini|deepseek|zhipu|gpt", model_name?: str}
    Header: X-Tenant-Id, X-User-Id（当 scope=user 时必须）"""

    def post(self, request: HttpRequest):
        body = get_json(request, {})
        scope = (body.get("scope") or "user").lower()
        provider = (body.get("provider") or "").lower().strip()
        model_name = (body.get("model_name") or "").strip() or None
        tenant_id = request.headers.get("X-Tenant-Id") or body.get("tenant_id")
        user_id = request.headers.get("X-User-Id") or body.get("user_id")
        if not tenant_id:
            return fail("Missing tenant_id", status=400)
        if scope == "user":
            if not user_id:
                return fail("Missing user_id", status=400)
            try:
                data = set_user_model(tenant_id=tenant_id, user_id=user_id, provider=provider, model_name=model_name)
                return ok(data)
            except Exception as e:  # 捕获无效 provider 等
                return fail(str(e), status=400)
        elif scope == "tenant":
            try:
                data = set_tenant_default_model(tenant_id=tenant_id, provider=provider, model_name=model_name)
                return ok(data)
            except Exception as e:
                return fail(str(e), status=400)
        return fail("Invalid scope", status=400)

