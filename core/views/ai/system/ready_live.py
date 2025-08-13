# file: core/views/ai/system/ready_live.py
# purpose: 存活/就绪探针：/live/ 永远 200；/ready/ 依赖数据库与缓存等基础组件
from __future__ import annotations
from django.views import View
from django.http import HttpRequest
from core.views.utils import ok, fail
from core.ai.diagnostics import check_database, check_cache


class AiLiveView(View):
    """GET /api/ai/system/live/ → 总是 200（仅用于容器存活探针）。"""

    def get(self, request: HttpRequest):
        return ok({"ok": True})


class AiReadyView(View):
    """GET /api/ai/system/ready/ → 基础依赖可用才返回 200。"""

    def get(self, request: HttpRequest):
        try:
            c1 = check_database()
            c2 = check_cache()
            ok_all = c1.ok and c2.ok
            if not ok_all:
                return fail("not ready", status=503, data={"items": [c1.to_dict(), c2.to_dict()]})
            return ok({"ok": True})
        except Exception as e:
            return fail(str(e), status=503)


