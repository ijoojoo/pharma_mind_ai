# file: core/logging/json.py
# purpose: 结构化 JSON 日志格式器（含 request_id）；提供 setup_json_logging() 便于在 settings 中启用
from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict
from core.middleware.request_id import REQUEST_ID_CTX


class JsonLogFormatter(logging.Formatter):
    """将日志记录输出为单行 JSON，字段：ts, level, logger, msg, request_id, extra..."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": REQUEST_ID_CTX.get(),
        }
        # 透传 extra 字段
        for k, v in record.__dict__.items():
            if k in ("msg", "args", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"):
                continue
            if k.startswith("_"):
                continue
            payload[k] = v
        return json.dumps(payload, ensure_ascii=False)


def setup_json_logging():
    """在 settings.py 中调用以开启 JSON 日志输出。"""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))


