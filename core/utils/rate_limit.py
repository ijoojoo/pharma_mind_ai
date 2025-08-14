# file: core/utils/rate_limit.py
# purpose: 轻量级限速器（进程内内存版），提供按租户令牌桶；已在中间件层有更强限流时，此工具可选用在批量任务中。

from __future__ import annotations
import time
from typing import Dict


class TokenBucket:
    """令牌桶实现：capacity/ refill_rate（每秒产生多少令牌）。"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = max(1, int(capacity))
        self.refill_rate = max(0.1, float(refill_rate))
        self.tokens = float(self.capacity)
        self.updated = time.monotonic()

    def allow(self, cost: float = 1.0) -> bool:
        """尝试消费令牌，成功返回 True。"""
        now = time.monotonic()
        # 回填
        delta = now - self.updated
        self.updated = now
        self.tokens = min(self.capacity, self.tokens + delta * self.refill_rate)
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False


class RateLimiter:
    """按 tenant_id 管理的简单限速器。"""

    def __init__(self, capacity: int = 30, refill_rate: float = 0.5):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, TokenBucket] = {}

    def is_allowed(self, tenant_id: str, cost: float = 1.0) -> bool:
        b = self.buckets.get(tenant_id)
        if not b:
            b = self.buckets[tenant_id] = TokenBucket(self.capacity, self.refill_rate)
        return b.allow(cost)


# 单例（可直接导入使用）
rate_limiter = RateLimiter()
