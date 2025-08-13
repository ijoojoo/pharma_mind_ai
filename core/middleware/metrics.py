# file: core/middleware/metrics.py
# purpose: 请求指标采集（/api/ai/**）：请求计数 + 时延直方图 + 慢请求告警
from __future__ import annotations
import time
from typing import Callable
from django.http import HttpRequest
from django.conf import settings
import logging

from core.observability.metrics import inc_request, observe_latency

logger = logging.getLogger("ai.slow")


def _route_label(req: HttpRequest) -> str:
    try:
        m = req.resolver_match
        if m and m.view_name:
            return str(m.view_name)
    except Exception:
        pass
    # 退化：/api/ai/<a>/<b>/
    p = (req.path or "/").strip("/").split("/")
    if len(p) >= 4 and p[0] == "api" and p[1] == "ai":
        return f"{p[2]}/{p[3]}"  # e.g. system/health
    if len(p) >= 3 and p[0] == "api" and p[1] == "ai":
        return f"{p[2]}"
    return "unknown"


class RequestMetricsMiddleware:
    """为 /api/ai/ 路径采集基础指标，并在 header 中附带 X-Request-Duration（毫秒）。"""

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.slow_ms = int(getattr(settings, "AI_SLOW_MS", 1500))

    def __call__(self, request: HttpRequest):
        if not (request.path or "").startswith("/api/ai/"):
            return self.get_response(request)
        t0 = time.perf_counter()
        route = _route_label(request)
        method = request.method.upper()
        response = self.get_response(request)
        dt = time.perf_counter() - t0
        # 指标
        try:
            inc_request(method, route, getattr(response, "status_code", 0))
            observe_latency(method, route, dt)
        except Exception:
            pass
        # 慢请求日志
        if (dt * 1000.0) >= self.slow_ms:
            try:
                logger.warning("slow_request", extra={"route": route, "method": method, "duration_ms": int(dt * 1000)})
            except Exception:
                pass
        # 响应头
        try:
            response["X-Request-Duration"] = str(int(dt * 1000))
        except Exception:
            pass
        return response
