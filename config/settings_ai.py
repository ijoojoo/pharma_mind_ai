# file: config/settings_ai.py
# purpose: 统一的 AI 配置中心
# 用途：集中读取/解析环境变量，形成结构化配置，并把关键项注入 Django settings（settings.AI_*）。
# 兼容性：保留 settings.LLM_PROVIDER（旧代码使用）；其余以 settings.AI_* 命名。

from __future__ import annotations
import os
import json
from typing import Any, Dict, Optional

try:
    # 可选：加载 .env（若已由外层加载可忽略）
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()  # 不报错，静默处理
except Exception:
    pass


# --------------------- 基础解析工具 ---------------------

def _getenv(key: str, default: Optional[str] = None) -> Optional[str]:
    """安全读取环境变量，空字符串视为 None。"""
    v = os.getenv(key)
    if v is None:
        return default
    v2 = v.strip()
    return v2 if v2 != "" else (default if default != "" else None)


def _as_bool(v: Any, default: bool = False) -> bool:
    """将多种字符串形式转为布尔。"""
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def _as_int(v: Any, default: int = 0) -> int:
    """将字符串/数字转为 int，失败返回默认值。"""
    try:
        return int(float(v))
    except Exception:
        return default


def _as_json(v: Any, default: Any = None) -> Any:
    """解析 JSON 字符串，失败返回默认值。"""
    if v is None:
        return default
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(str(v))
    except Exception:
        return default


# --------------------- 统一构建配置 ---------------------

def _normalize_provider(name: Optional[str]) -> str:
    """轻量 provider 规范化（与 llm.registry 的严格版保持一致语义：小写、去连字符、别名）。"""
    if not name:
        return "mock"
    s = str(name).strip().lower().replace(" ", "").replace("-", "")
    alias = {
        "openai": "gpt",
        "chatgpt": "gpt",
        "gpt4": "gpt",
        "gpt4o": "gpt",
        "deepseek": "deepseek",
        "deepseekai": "deepseek",
        "deepseekchat": "deepseek",
        "zhipu": "zhipu",
        "zhipuai": "zhipu",
        "glm": "zhipu",
        "google": "gemini",
        "gemini": "gemini",
        "mock": "mock",
        "dummy": "mock",
        "test": "mock",
    }
    return alias.get(s, s if s in {"gpt", "gemini", "deepseek", "zhipu", "mock"} else "mock")


def build_ai_config() -> Dict[str, Any]:
    """读取环境变量，组装统一 AI 配置字典（不写入 settings，仅返回 dict）。"""
    default_provider = _normalize_provider(_getenv("LLM_PROVIDER", "gpt"))

    cfg: Dict[str, Any] = {
        # 总开关类
        "metrics_enabled": _as_bool(_getenv("AI_METRICS_ENABLED", "1"), True),
        "slow_ms": _as_int(_getenv("AI_SLOW_MS", "1500"), 1500),
        "log_retention_days": _as_int(_getenv("AI_LOG_RETENTION_DAYS", "90"), 90),
        # 限流
        "rate_limit": {
            "tenant_limit": _as_int(_getenv("AI_RL_TENANT_LIMIT", "60"), 60),
            "user_limit": _as_int(_getenv("AI_RL_USER_LIMIT", "30"), 30),
            "window": _as_int(_getenv("AI_RL_WINDOW", "60"), 60),
        },
        # 供应商与模型
        "llm": {
            "default_provider": default_provider,
            "providers": {
                "gpt": {
                    "api_key": _getenv("OPENAI_API_KEY"),
                    "base_url": _getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    "model": _getenv("GPT_MODEL", "gpt-4o-mini"),
                },
                "gemini": {
                    "api_key": _getenv("GEMINI_API_KEY"),
                    "base_url": _getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com"),
                    "model": _getenv("GEMINI_MODEL", "gemini-1.5-pro-latest"),
                },
                "deepseek": {
                    "api_key": _getenv("DEEPSEEK_API_KEY"),
                    "base_url": _getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                    "model": _getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                },
                "zhipu": {
                    "api_key": _getenv("ZHIPU_API_KEY"),
                    "base_url": _getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn"),
                    "model": _getenv("ZHIPU_MODEL", "glm-4"),
                },
                "mock": {
                    "api_key": None,
                    "base_url": None,
                    "model": "mock-echo",
                },
            },
        },
        # 账单通知：{"*": ["ops@example.com"], "tenantA": ["a@x"]}
        "billing_notify_emails": _as_json(_getenv("AI_BILLING_NOTIFY_EMAILS"), {}) or {},
    }
    # 兼容性：把默认 provider 也放到顶层（便于 settings.LLM_PROVIDER）
    cfg["llm_provider"] = default_provider
    return cfg


def apply_ai_settings(settings_globals: Dict[str, Any]) -> Dict[str, Any]:
    """把 AI 配置写入 Django settings（传入 settings.py 的 globals()）。
    - 注入：AI_LLM（含 default_provider/providers），AI_RATE_LIMIT，AI_METRICS_ENABLED，AI_SLOW_MS，AI_LOG_RETENTION_DAYS，AI_BILLING_NOTIFY_EMAILS
    - 保留：LLM_PROVIDER（兼容旧代码）
    返回注入的字典副本，便于调试。
    """
    cfg = build_ai_config()
    settings_globals["AI_LLM"] = cfg["llm"]
    settings_globals["AI_RATE_LIMIT"] = cfg["rate_limit"]
    settings_globals["AI_METRICS_ENABLED"] = cfg["metrics_enabled"]
    settings_globals["AI_SLOW_MS"] = cfg["slow_ms"]
    settings_globals["AI_LOG_RETENTION_DAYS"] = cfg["log_retention_days"]
    settings_globals["AI_BILLING_NOTIFY_EMAILS"] = cfg["billing_notify_emails"]
    # 旧字段（仍被部分代码读取）
    settings_globals["LLM_PROVIDER"] = cfg["llm_provider"]
    return {
        "LLM_PROVIDER": settings_globals["LLM_PROVIDER"],
        "AI_LLM": settings_globals["AI_LLM"],
        "AI_RATE_LIMIT": settings_globals["AI_RATE_LIMIT"],
        "AI_METRICS_ENABLED": settings_globals["AI_METRICS_ENABLED"],
        "AI_SLOW_MS": settings_globals["AI_SLOW_MS"],
        "AI_LOG_RETENTION_DAYS": settings_globals["AI_LOG_RETENTION_DAYS"],
        "AI_BILLING_NOTIFY_EMAILS": settings_globals["AI_BILLING_NOTIFY_EMAILS"],
    }


# 可选：在独立运行时打印调试（不会在 Django 导入时执行）
if __name__ == "__main__":  # pragma: no cover
    import pprint
    pprint.pp(build_ai_config())
