# file: config/settings_patch_ai.py
# purpose: 无侵入方式为现有项目 settings 注入中间件与 env 配置；在 settings.py 末尾 `from .settings_patch_ai import *`
from __future__ import annotations

# 引入环境变量映射（不会覆盖已有 settings，除非同名）
from .setting_env import *  # noqa

try:
    # 尝试扩展 MIDDLEWARE：插入到 SecurityMiddleware 之后，以确保 Header 可被后续中间件使用
    MIDDLEWARE  # type: ignore  # noqa
except NameError:
    MIDDLEWARE = []  # type: ignore

# 待注入列表（按顺序）
_ai_middlewares = [
    "core.middleware.tenant.TenantMiddleware",
    "core.middleware.auth.ApiKeyAuthMiddleware",
    "core.middleware.ratelimit.RateLimitMiddleware",
]

for mw in _ai_middlewares:
    if mw not in MIDDLEWARE:
        MIDDLEWARE.append(mw)