# file: core/utils/retry.py
# purpose: 通用重试工具（指数退避 + 抖动）；供外部在调用不稳定 LLM/HTTP 时复用。

from __future__ import annotations
import random
import time
from typing import Callable, TypeVar, Any

T = TypeVar("T")


def retry(fn: Callable[[], T], *, attempts: int = 3, base_delay: float = 0.8, max_delay: float = 8.0) -> T:
    """对无参函数进行重试；失败抛出最后一次异常。
    - attempts: 最大重试次数（含首次）
    - base_delay: 初始等待秒数，之后指数退避 ×2，并加 0~30% 抖动
    - max_delay: 单次最大等待秒数
    """
    last: Exception | None = None
    delay = max(0.05, float(base_delay))
    for i in range(max(1, attempts)):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            if i >= attempts - 1:
                break
            jitter = 1.0 + random.random() * 0.3
            time.sleep(min(max_delay, delay * jitter))
            delay = min(max_delay, delay * 2.0)
    assert last is not None
    raise last