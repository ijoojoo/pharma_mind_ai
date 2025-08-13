# file: core/views/ai/system/env.py
# purpose: 环境探针与模型生效信息；前端可用来判断环境/后端能力与默认模型
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from django.conf import settings
from core.views.utils import ok, fail
from core.ai.model_prefs import get_effective_model, list_supported_providers


class AiEnvView(View):
    """GET /api/ai/system/env/ → 返回后端环境/版本、启用的提供商列表、当前默认模型（解析链：用户>租户>环境>回退）。"""

    def get(self, request: HttpRequest):
        try:
            tenant_id = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id") or "_"
            user_id = request.headers.get("X-User-Id") or request.GET.get("user_id")
            env_provider = getattr(settings, "LLM_PROVIDER", None)
            eff = get_effective_model(tenant_id=tenant_id, user_id=user_id, env_provider=env_provider)
            providers = list_supported_providers()
            data = {
                "backend": {
                    "version": getattr(settings, "APP_VERSION", "unknown"),
                    "env": getattr(settings, "ENV", "dev"),
                },
                "providers": providers,
                "effective_model": eff.to_dict(),
            }
            return ok(data)
        except Exception as e:
            return fail(str(e))


