# file: core/ai/ops/notify.py
# purpose: 通知下发器：将新/更新的事件按通道发送（邮件/Webhook）；供管理命令与视图调用
from __future__ import annotations
from typing import List, Dict, Any
from django.conf import settings
from django.core.mail import send_mail

try:
    import requests  # 可选依赖；若缺失则回退 urllib
except Exception:  # pragma: no cover
    requests = None  # type: ignore
import json
from urllib import request as urlrequest

from core.models.ai_ops import OpsAlertChannel


def _fmt_email_body(tenant_id: str, items: List[Dict[str, Any]]) -> str:
    """构造简易文本邮件正文。"""
    lines = [f"Tenant: {tenant_id}", f"Count: {len(items)}", ""]
    for it in items[:50]:  # 防止过长
        lines.append(f"- [{it.get('severity')}] {it.get('type')} {it.get('group')} → {it.get('today', it.get('qty', ''))}")
    return "\n".join(lines)


def _send_email(to_list: List[str], subject: str, body: str) -> None:
    """发送邮件；失败时静默（记录由上层捕获）。"""
    if not to_list:
        return
    send_mail(subject=subject, message=body, from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None), recipient_list=to_list, fail_silently=True)


def _send_webhook(url: str, payload: Dict[str, Any], headers: Dict[str, str] | None = None, timeout: int = 10) -> None:
    """发送 Webhook：优先用 requests；缺失则使用 urllib 回退。"""
    data = json.dumps(payload).encode("utf-8")
    if requests:  # pragma: no cover
        try:
            requests.post(url, json=payload, headers=headers or {}, timeout=timeout)
            return
        except Exception:
            return
    # urllib 回退
    req = urlrequest.Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        urlrequest.urlopen(req, timeout=timeout)  # nosec - 仅出站
    except Exception:
        return


def notify_incidents(*, tenant_id: str, items: List[Dict[str, Any]]) -> int:
    """对租户的所有激活通道下发事件汇总。返回成功通道数（静默失败不抛）。"""
    chans = list(OpsAlertChannel.objects.filter(tenant_id=tenant_id, is_active=True))
    if not chans or not items:
        return 0
    ok = 0
    for ch in chans:
        try:
            if ch.kind == "email":
                to_list = list((ch.config or {}).get("to") or [])
                _send_email(to_list, subject="OPS 异常告警", body=_fmt_email_body(tenant_id, items))
                ok += 1
            elif ch.kind == "webhook":
                cfg = ch.config or {}
                _send_webhook(cfg.get("url") or "", {"tenant_id": tenant_id, "items": items}, headers=cfg.get("headers") or {})
                ok += 1
        except Exception:
            # 保留 last_error 但不影响其他通道
            ch.last_error = "send failed"
            ch.save(update_fields=["last_error"])
    return ok