# file: core/views/utils.py
# purpose: 统一 API/请求工具：ok()/fail()/bad_request()/get_json() +
#          get_enterprise()/get_date_range_from_request()/is_range_mode()/hour_labels()
from __future__ import annotations
from typing import Any, Dict, Optional, Tuple, List
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from datetime import datetime, date, timedelta
import json


# ---- Response helpers -------------------------------------------------------

def ok(data: Any = None, *, status: int = 200, **headers) -> JsonResponse:
    """标准成功响应: {"success": true, "data": ...}"""
    payload: Dict[str, Any] = {"success": True, "data": data}
    resp = JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})
    for k, v in headers.items():
        try:
            resp[k] = str(v)
        except Exception:
            pass
    return resp


def fail(message: str, *, status: int = 400, code: str = "bad_request", data: Any = None, **headers) -> JsonResponse:
    """标准失败响应: {"success": false, "error": {code,message}, "data"?}"""
    payload: Dict[str, Any] = {"success": False, "error": {"code": code, "message": str(message)}}
    if data is not None:
        payload["data"] = data
    resp = JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})
    for k, v in headers.items():
        try:
            resp[k] = str(v)
        except Exception:
            pass
    return resp


def bad_request(message: str = "Bad request", *, data: Any = None) -> JsonResponse:
    """便捷 400 响应（与旧代码兼容）。"""
    return fail(message, status=400, code="bad_request", data=data)


# ---- Request helpers --------------------------------------------------------

def get_json(request: HttpRequest, default: Optional[dict] = None) -> dict:
    """安全读取 JSON 请求体；若不是 JSON 或解析失败，回退到表单。"""
    default = {} if default is None else default
    ctype = (request.headers.get("Content-Type") or request.META.get("CONTENT_TYPE") or "").lower()
    body = request.body or b""
    if body:
        try:
            if "application/json" in ctype or ctype.startswith("application/json"):
                return json.loads(body.decode("utf-8"))
            # 有些客户端没带 content-type，仍尝试按 JSON 解析
            return json.loads(body.decode("utf-8"))
        except Exception:
            pass
    if getattr(request, "POST", None):
        return {k: v for k, v in request.POST.items()}
    return dict(default)


# 可用于装饰无需 CSRF 的纯 API 视图
api_exempt = csrf_exempt


# ---- Common UI helpers ------------------------------------------------------

def get_enterprise(request: HttpRequest, *, required: bool = False) -> Dict[str, Optional[str]]:
    """返回企业/租户上下文。
    - 优先从请求头 `X-Tenant-Id` / `X-User-Id`
    - 也支持 TenantMiddleware 注入的 `request.tenant_id`
    - 用户 ID 尝试从 `request.user` 获取
    返回: {"tenant_id": str|None, "user_id": str|None}
    """
    tenant_id = request.headers.get("X-Tenant-Id") or getattr(request, "tenant_id", None)
    # 用户 ID: header 或鉴权用户
    user_id = request.headers.get("X-User-Id")
    if not user_id and hasattr(request, "user") and request.user and not isinstance(request.user, AnonymousUser):
        try:
            user_id = str(getattr(request.user, "id", None) or getattr(request.user, "pk", None) or getattr(request.user, "username", None) or "") or None
        except Exception:
            user_id = None
    if required and not tenant_id:
        raise ValueError("Missing tenant_id (X-Tenant-Id)")
    return {"tenant_id": tenant_id, "user_id": user_id}


def _parse_date(s: str | None) -> Optional[date]:
    if not s:
        return None
    try:
        # 优先 YYYY-MM-DD
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            return datetime.fromisoformat(s).date()
        # 其他 ISO 形式
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


def get_date_range_from_request(request: HttpRequest, *, default_days: int = 7) -> Tuple[date, date]:
    """从请求参数解析日期范围。
    支持: start/end 或 from/to 或单个 date。
    若均未提供，默认取 [今天-default_days+1, 今天]。
    返回: (start_date, end_date)
    """
    params = {}
    if request.method.upper() == "GET":
        params = request.GET
    else:
        try:
            params = get_json(request)
        except Exception:
            params = request.POST or {}

    start = _parse_date(params.get("start") or params.get("from"))
    end = _parse_date(params.get("end") or params.get("to"))
    single = _parse_date(params.get("date"))
    days_param = params.get("days")

    today = timezone.localdate()

    if single and not (start or end):
        return single, single

    if start and end:
        if end < start:
            start, end = end, start
        return start, end

    if start and not end:
        return start, start

    if end and not start:
        return end, end

    # 未提供 → 回退 days
    try:
        d = int(days_param)
        if d > 0:
            start = today - timedelta(days=d - 1)
            end = today
            return start, end
    except Exception:
        pass

    start = today - timedelta(days=max(1, int(default_days)) - 1)
    end = today
    return start, end


def is_range_mode(request: HttpRequest, start: Optional[date] = None, end: Optional[date] = None) -> bool:
    """是否区间模式（用于 UI 决定按天/按小时）。
    规则：显式 mode=range / range=1，或 start!=end，或 days>1 即为 True。
    """
    params = request.GET if request.method.upper() == "GET" else (get_json(request, {}) or {})
    mode = str(params.get("mode") or "").lower()
    if mode in ("range", "r"):
        return True
    if str(params.get("range") or "") in ("1", "true", "True"):
        return True
    try:
        if int(params.get("days", 0)) > 1:
            return True
    except Exception:
        pass
    if start is not None and end is not None and start != end:
        return True
    return False


def hour_labels() -> List[str]:
    """返回 24 小时标签数组：['00:00', '01:00', ... '23:00']"""
    return [f"{i:02d}:00" for i in range(24)]
