# file: core/observability/metrics.py
# purpose: 轻量级 Prometheus 指标注册与导出（内存版，无第三方依赖）
# - 提供 Counter/Histogram；支持 labels（最多 5 个维度，避免爆炸）
# - RequestMetricsMiddleware 会用到；也可在业务处调用 inc_tokens() 等自定义指标
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, List, Iterable
import threading
import time


# -------- Registry --------

class MetricRegistry:
    """进程内全局注册表（线程安全）。"""

    def __init__(self):
        self._lock = threading.RLock()
        self._counters: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {}
        self._hist_sum: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {}
        self._hist_cnt: Dict[str, Dict[Tuple[Tuple[str, str], ...], float]] = {}
        self._hist_buckets: Dict[str, List[float]] = {}
        self._hist_bucket_vals: Dict[str, Dict[Tuple[Tuple[str, str], ...], List[float]]] = {}

    def counter_inc(self, name: str, labels: Dict[str, str] | None = None, value: float = 1.0):
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._counters.setdefault(name, {})
            self._counters[name][key] = self._counters[name].get(key, 0.0) + float(value)

    def histogram_observe(self, name: str, value: float, *, buckets: Iterable[float], labels: Dict[str, str] | None = None):
        key = tuple(sorted((labels or {}).items()))
        b = list(buckets)
        with self._lock:
            self._hist_buckets.setdefault(name, b)
            self._hist_sum.setdefault(name, {})
            self._hist_cnt.setdefault(name, {})
            self._hist_bucket_vals.setdefault(name, {})
            self._hist_sum[name][key] = self._hist_sum[name].get(key, 0.0) + float(value)
            self._hist_cnt[name][key] = self._hist_cnt[name].get(key, 0.0) + 1.0
            arr = self._hist_bucket_vals[name].setdefault(key, [0.0] * (len(b) + 1))
            # 直方图为累积桶；这里先按原始桶计数，导出时累积
            placed = False
            for i, up in enumerate(b):
                if value <= up:
                    arr[i] += 1.0
                    placed = True
                    break
            if not placed:
                arr[-1] += 1.0  # +Inf

    # ---- exposition ----
    def _render_labels(self, labels: Tuple[Tuple[str, str], ...]) -> str:
        if not labels:
            return ""
        parts = [f"{k}={self._esc(v)}" for k, v in labels]
        return "{" + ",".join(parts) + "}"

    @staticmethod
    def _esc(v: str) -> str:
        s = str(v).replace("\\", "\\\\").replace("\n", "\\n").replace("\"", "\\\"")
        return f'"{s}"'

    def export_prometheus(self) -> str:
        """导出为 Prometheus 文本格式。"""
        lines: List[str] = []
        now_ms = int(time.time() * 1000)
        with self._lock:
            # counters
            for name, entries in self._counters.items():
                lines.append(f"# TYPE {name} counter")
                for labels, val in entries.items():
                    lines.append(f"{name}{self._render_labels(labels)} {val} {now_ms}")
            # histograms
            for name, entries in self._hist_cnt.items():
                buckets = self._hist_buckets.get(name, [])
                lines.append(f"# TYPE {name} histogram")
                for labels, cnt in entries.items():
                    arr = list(self._hist_bucket_vals[name][labels])
                    cum = 0.0
                    # 累积桶（le=...）
                    for i, up in enumerate(buckets):
                        cum += arr[i]
                        lines.append(f"{name}_bucket{self._render_labels(tuple(sorted(labels + ((('le', str(up)),)))))} {cum} {now_ms}")
                    # +Inf
                    cum += arr[-1]
                    lines.append(f"{name}_bucket{self._render_labels(tuple(sorted(labels + ((('le', '+Inf'),)))))} {cum} {now_ms}")
                    # sum/count
                    s = self._hist_sum[name][labels]
                    c = self._hist_cnt[name][labels]
                    lines.append(f"{name}_sum{self._render_labels(labels)} {s} {now_ms}")
                    lines.append(f"{name}_count{self._render_labels(labels)} {c} {now_ms}")
        return "\n".join(lines) + "\n"


REGISTRY = MetricRegistry()

# 预定义指标名/桶
HTTP_REQ_TOTAL = "ai_http_requests_total"
HTTP_REQ_SECONDS = "ai_http_request_duration_seconds"
DEFAULT_BUCKETS = [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]

# 自定义：Token 消耗
TOKENS_SPENT_TOTAL = "ai_tokens_spent_total"  # labels: tenant, provider


def inc_request(method: str, route: str, status: int):
    REGISTRY.counter_inc(HTTP_REQ_TOTAL, {"method": method, "route": route, "status": str(status)})


def observe_latency(method: str, route: str, seconds: float):
    REGISTRY.histogram_observe(HTTP_REQ_SECONDS, seconds, buckets=DEFAULT_BUCKETS, labels={"method": method, "route": route})


def inc_tokens(tenant: str, provider: str, n: int):
    REGISTRY.counter_inc(TOKENS_SPENT_TOTAL, {"tenant": tenant, "provider": provider}, value=float(n))
