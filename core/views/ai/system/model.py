# file: core/views/ai/system/model.py
# purpose: 模型提供商与偏好设置 API（用户级与租户级）；配合 core/ai/model_prefs.py
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail, get_json, get_enterprise
from core.ai.model_prefs import (
    list_supported_providers,
    get_effective_model,
    get_user_model,
    set_user_model,
    get_tenant_default_model,
    set_tenant_default_model,
    InvalidProvider,
)


class ModelProviderListView(View):
    """GET /api/ai/system/model/providers/
    返回支持的 Provider 列表（key/name/default_model）
    """
    def get(self, request: HttpRequest):
        try:
            return ok({"providers": list_supported_providers()})
        except Exception as e:
            return fail(str(e))


class ModelPreferenceView(View):
    """GET/POST /api/ai/system/model/preference/
    GET : 返回当前用户的模型偏好与最终生效模型（含解析来源）
    POST: 设置用户偏好 {provider, model_name?}
    """
    def get(self, request: HttpRequest):
        try:
            ent = get_enterprise(request, required=True)
            tenant_id = ent["tenant_id"]
            user_id = ent.get("user_id") or request.GET.get("user_id")
            if not user_id:
                return fail("Missing user_id", status=400)
            pref = get_user_model(tenant_id=tenant_id, user_id=user_id)
            eff = get_effective_model(tenant_id=tenant_id, user_id=user_id)
            return ok({"preference": pref, "effective": eff.to_dict()})
        except Exception as e:
            return fail(str(e))

    def post(self, request: HttpRequest):
        try:
            ent = get_enterprise(request, required=True)
            tenant_id = ent["tenant_id"]
            user_id = ent.get("user_id")
            payload = get_json(request)
            user_id = payload.get("user_id") or user_id
            if not user_id:
                return fail("Missing user_id", status=400)
            provider = payload.get("provider")
            model_name = payload.get("model_name")
            if not provider:
                return fail("Missing provider", status=400)
            data = set_user_model(tenant_id=tenant_id, user_id=str(user_id), provider=provider, model_name=model_name)
            eff = get_effective_model(tenant_id=tenant_id, user_id=str(user_id))
            return ok({"preference": data, "effective": eff.to_dict()})
        except InvalidProvider as e:
            return fail(str(e), status=400)
        except Exception as e:
            return fail(str(e))


class TenantDefaultModelView(View):
    """GET/POST /api/ai/system/model/tenant_default/
    GET : 返回租户默认模型
    POST: 设置租户默认模型 {provider, model_name?}
    """
    def get(self, request: HttpRequest):
        try:
            ent = get_enterprise(request, required=True)
            tenant_id = ent["tenant_id"]
            data = get_tenant_default_model(tenant_id=tenant_id)
            return ok({"tenant_default": data})
        except Exception as e:
            return fail(str(e))

    def post(self, request: HttpRequest):
        try:
            ent = get_enterprise(request, required=True)
            tenant_id = ent["tenant_id"]
            payload = get_json(request)
            provider = payload.get("provider")
            model_name = payload.get("model_name")
            if not provider:
                return fail("Missing provider", status=400)
            data = set_tenant_default_model(tenant_id=tenant_id, provider=provider, model_name=model_name)
            eff = get_effective_model(tenant_id=tenant_id)
            return ok({"tenant_default": data, "effective": eff.to_dict()})
        except InvalidProvider as e:
            return fail(str(e), status=400)
        except Exception as e:
            return fail(str(e))
