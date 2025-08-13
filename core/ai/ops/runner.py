# file: core/ai/ops/runner.py
# purpose: 规则扫描执行器：从 DB 读取启用规则 → 调用检测 → 合并/落库事件 → 返回本次命中
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from django.db import transaction
from django.utils import timezone

from core.models.ai_ops import OpsAlertRule, OpsIncident
from core.ai.ops.anomaly_rules import detect_anomalies


def _incident_key(rule_type: str, group: Dict[str, Any]) -> str:
    """构造事件归一化键：<type>|k1=v1|k2=v2（顺序稳定）。"""
    parts = [rule_type]
    for k in sorted((group or {}).keys()):
        parts.append(f"{k}={group.get(k)}")
    return "|".join(parts)


def run_ops_scan(*, tenant_id: str, window: Dict[str, Any], extra_rules: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    """执行一次扫描：
    1) 读取启用中的规则（该租户）
    2) 合并 extra_rules（可由 API 临时传入）
    3) 调用 detect_anomalies 得到命中明细
    4) 按 (rule, group) 合并入库/更新事件
    返回：本次命中的明细列表（带 incident_id）
    """
    active = list(OpsAlertRule.objects.filter(tenant_id=tenant_id, is_active=True).values("id", "type", "config"))
    rules = []
    for r in active:
        rules.append({"id": r["id"], "type": r["type"], **(r.get("config") or {})})
    for er in extra_rules or []:
        rules.append(er)

    hits = detect_anomalies(tenant_id=tenant_id, window=window or {}, rules=rules)
    out: List[Dict[str, Any]] = []
    now = timezone.now()
    with transaction.atomic():
        for it in hits:
            rid = it.get("rule_id")
            rtype = it.get("type")
            group = it.get("group") or {}
            sev = str(it.get("severity") or "medium")
            key = _incident_key(rtype, group)
            rule_obj = OpsAlertRule.objects.filter(id=rid).first()
            if not rule_obj:
                # 兼容临时 extra_rule：尝试匹配同类型第一条规则，否则跳过落库但仍返回
                rule_obj = OpsAlertRule.objects.filter(tenant_id=tenant_id, type=rtype, is_active=True).first()
            inc = OpsIncident.objects.filter(tenant_id=tenant_id, key=key).first()
            if inc:
                inc.severity = sev
                inc.last_seen = now
                inc.hit_count = (inc.hit_count or 0) + 1
                inc.payload = it
                inc.status = "open" if inc.status != "closed" else inc.status  # 已关闭则保持关闭
                inc.save(update_fields=["severity", "last_seen", "hit_count", "payload", "status"])
            else:
                inc = OpsIncident.objects.create(
                    tenant_id=tenant_id,
                    rule=rule_obj if rule_obj else None,  # type: ignore
                    key=key,
                    severity=sev,
                    status="open",
                    payload=it,
                    first_seen=now,
                    last_seen=now,
                    hit_count=1,
                )
            it["incident_id"] = inc.id
            out.append(it)
    return out