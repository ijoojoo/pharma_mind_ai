# file: config/settings_ai.py
# purpose: 扩展/示例配置（追加到现有 settings_ai.py 中或在主 settings 覆盖）。
# 注意：此文件为完整片段（含上一阶段的 CORS/限流/日志保留期），可直接导入：from .settings_ai import *

# —— CORS ——
AI_CORS = {
    "allow_origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
    "allow_methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Tenant-Id", "X-User-Id", "X-Api-Key", "X-Signature", "X-Timestamp", "X-Nonce"],
    "expose_headers": ["X-RateLimit-Remaining"],
    "allow_credentials": True,
    "max_age": 600,
}

# —— 限流/日志 ——
AI_RATE_LIMIT = {"tenant_limit": 60, "user_limit": 30, "window": 60}
AI_LOG_RETENTION_DAYS = 90

# —— 签名校验 ——
AI_SIGNING = {
    "enabled": False,       # 默认关闭；联调稳定后再开启
    "clock_skew": 300,      # 允许 5 分钟时间漂移
    "nonce_ttl": 600,       # nonce 生存时间
    "keys": {
        # 示例：为前端/第三方分配 key/secret；可选 tenant 绑定
        # "demo-key": {"secret": "demo-secret", "tenant_id": "demo-tenant"},
        # "*": {"secret": "public-secret"},   # 通配（不建议生产使用）
    },
}

# —— 请求体大小限制 ——
AI_MAX_REQUEST_BYTES = 1 * 1024 * 1024  # 1MB

# —— 版本/环境（供 /api/ai/system/env/ 使用）——
APP_VERSION = "1.0.0"
ENV = "dev"


# - AI_METRICS_ENABLED: 是否开启 /metrics 暴露
# - AI_SLOW_MS: 慢请求阈值（毫秒），RequestMetricsMiddleware 会按此阈值打日志

AI_METRICS_ENABLED = True
AI_SLOW_MS = 1500  # 1.5s 视为慢请求


