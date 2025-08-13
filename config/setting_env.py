# file: config/settings_env.py
# purpose: 统一从环境变量加载 AI 相关配置（带默认值），供 settings 使用
from __future__ import annotations
import os
import json

# 默认 Provider：mock|gpt|gemini|deepseek|zhipu
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")

# OpenAI 兼容（gpt）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE = os.getenv("OPENAI_BASE", "")  # 例如 https://api.openai.com

# Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_API_BASE = os.getenv("GOOGLE_API_BASE", "")

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "")

# Zhipu GLM
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_API_BASE = os.getenv("ZHIPU_API_BASE", "")

# 低余额通知（JSON 字符串，如 '{"*": ["ops@example.com"]}' ）
try:
    AI_BILLING_NOTIFY_EMAILS = json.loads(os.getenv("AI_BILLING_NOTIFY_EMAILS", "{}"))
except Exception:
    AI_BILLING_NOTIFY_EMAILS = {}

# 限流（env 使用扁平命名，settings 里聚合为 dict）
AI_RATE_LIMIT = {
    "tenant_limit": int(os.getenv("AI_RATE_LIMIT__TENANT_LIMIT", "60")),
    "user_limit": int(os.getenv("AI_RATE_LIMIT__USER_LIMIT", "30")),
    "window": int(os.getenv("AI_RATE_LIMIT__WINDOW", "60")),  # seconds
}

# 邮件默认发件人（用于报警）
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")

# 日志保留天数（用于定时清理）
AI_LOG_RETENTION_DAYS = int(os.getenv("AI_LOG_RETENTION_DAYS", "90"))

# 可选：是否强制 /api/ai/ 走 API Key 鉴权（默认 False）
AI_REQUIRE_AUTH = os.getenv("AI_REQUIRE_AUTH", "false").lower() in ("1", "true", "yes")
# 可选：每个租户的 API Keys（JSON），例如 {"tenantA": ["k1", "k2"], "tenantB": "kX"}
try:
    AI_API_KEYS = json.loads(os.getenv("AI_API_KEYS", "{}"))
except Exception:
    AI_API_KEYS = {}