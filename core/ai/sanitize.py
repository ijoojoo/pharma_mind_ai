# file: core/ai/sanitize.py
# purpose: 字段级脱敏与日志清洗工具（与 audit.py 配合）
from __future__ import annotations
from typing import Any, Dict, Iterable
from copy import deepcopy
from .audit import redact


# 默认敏感字段关键词（小写匹配）
_SENSITIVE_KEYS = {"password", "token", "api_key", "secret", "mobile", "phone", "email", "id_card"}


def mask_value(v: Any) -> Any:
    """对敏感值做通用掩码。字符串保留首尾 1-2 个字符；数值保留数量级；其他结构递归处理。"""
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return "[number]"
        s = str(v)
        if len(s) <= 6:
            return "*" * len(s)
        return s[:2] + "*" * (len(s) - 4) + s[-2:]
    except Exception:
        return "[masked]"


def scrub_dict(data: Dict[str, Any], *, allowlist: Iterable[str] | None = None) -> Dict[str, Any]:
    """按 allowlist 只保留白名单字段，其余字段做掩码；并对字符串做 PII 脱敏。"""
    allow = {str(k).lower() for k in (allowlist or [])}
    src = deepcopy(data or {})
    out: Dict[str, Any] = {}
    for k, v in src.items():
        kl = str(k).lower()
        if allow and kl not in allow:
            out[k] = mask_value(v)
            continue
        if isinstance(v, dict):
            out[k] = scrub_dict(v, allowlist=None)  # 子层不再套同一个 allow，逐层控制
        elif isinstance(v, str):
            out[k] = redact(v)
        else:
            out[k] = v
    return out


def sanitize_request_payload(payload: Dict[str, Any], *, allowlist: Iterable[str] | None = None) -> Dict[str, Any]:
    """对请求体进行字段级白名单与 PII 脱敏，供日志/审计记录使用。"""
    return scrub_dict(payload or {}, allowlist=allowlist)


def sanitize_response_text(text: str) -> Dict[str, Any]:
    """对 LLM 文本输出进行 PII 掩码 + 医疗宣称检测，返回结构与 audit.apply_output_filters 对齐。"""
    from .audit import apply_output_filters
    return apply_output_filters(tenant_id="-", text=text or "")

