# file: core/ai/audit.py
# purpose: 内容审计与脱敏（PII 掩码 + 医疗宣称检查）；供 Orchestrator 输出过滤调用
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Dict, Any


_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:(?:\+?86[- ]?)?1[3-9]\d{9})|(?:\d{3,4}-\d{7,8})")
_ID = re.compile(r"\b\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]\b")

# 过度宣称/违规用语（示例，可拓展到词库）
_MED_CLAIM_PATTERNS = [
    re.compile(p) for p in [
        r"(包治百病|根治|永不复发|百分之百|无副作用)",
        r"(替代医生|替代处方|随意停药)",
        r"(孕妇|儿童).*(随便|均可)使用",
    ]
]


@dataclass
class AuditIssue:
    type: str  # pii|medical_claim
    message: str
    snippet: str
    severity: str  # low|medium|high


def redact(text: str) -> str:
    if not text:
        return text
    s = _EMAIL.sub("[email]", text)
    s = _PHONE.sub("[phone]", s)
    s = _ID.sub("[id]", s)
    return s


def validate_med_claims(text: str) -> List[AuditIssue]:
    issues: List[AuditIssue] = []
    if not text:
        return issues
    for rx in _MED_CLAIM_PATTERNS:
        m = rx.search(text)
        if m:
            issues.append(AuditIssue(type="medical_claim", message="不当医疗宣称", snippet=m.group(0), severity="high"))
    return issues


def apply_output_filters(*, tenant_id: str, text: str) -> Dict[str, Any]:
    redacted = redact(text)
    issues = validate_med_claims(redacted)
    out: Dict[str, Any] = {"text": redacted, "issues": [i.__dict__ for i in issues]}
    if issues:
        out["disclaimer"] = "以上内容仅供参考，非医疗建议，请咨询专业医生。"
    return out