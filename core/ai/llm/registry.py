# file: core/ai/llm/registry.py
# purpose: LLM 供应商注册表（元信息 + 规范化 + 适配器获取）。
# 功能：
#  - normalize_provider_key: 统一归一化（别名/大小写/连字符）
#  - has_provider / get_provider_meta: 校验与读取元信息
#  - list_providers: 供前端/接口列出可用 Provider
#  - get_adapter_class: 懒加载返回对应的适配器类（避免循环依赖）

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Type


@dataclass(frozen=True)
class ProviderMeta:
    """供应商元信息：用于配置展示与默认模型解析。"""
    key: str                    # 规范化后的 provider key（gpt/gemini/deepseek/zhipu/mock）
    label: str                  # 展示名称
    default_model: str          # 默认模型名
    aliases: tuple[str, ...] = ()  # 可识别的别名
    api_key_env: Optional[str] = None  # API Key 的环境变量名（如 OPENAI_API_KEY）
    base_url_env: Optional[str] = None # 可选的 Base URL 环境变量名
    notes: Optional[str] = None        # 备注（用于文档）

    def to_dict(self) -> Dict:
        """转换成 dict，供接口返回。"""
        d = asdict(self)
        return d


# --- 别名与规范化 ---
_ALIAS_MAP: Dict[str, str] = {
    # gpt/openai 系
    "openai": "gpt",
    "chatgpt": "gpt",
    "gpt4": "gpt",
    "gpt-4": "gpt",
    "gpt-4o": "gpt",
    "gpt5": "gpt",
    "gpt-5": "gpt",
    # deepseek
    "deep-seek": "deepseek",
    # zhipu / glm
    "zhipuai": "zhipu",
    "glm": "zhipu",
    # gemini
    "google": "gemini",
    # mock
    "dummy": "mock",
    "test": "mock",
}


def normalize_provider_key(name: Optional[str]) -> Optional[str]:
    """把用户输入的 Provider 名称规范化为 key。
    规则：去空格 & 小写 & 去连字符，按别名映射到统一 key。"""
    if not name:
        return None
    s = str(name).strip().lower()
    s = s.replace(" ", "").replace("-", "")
    # 先别名，再直接命中
    mapped = _ALIAS_MAP.get(s)
    if mapped:
        return mapped
    # 已是标准 key 的情况
    if s in ("gpt", "gemini", "deepseek", "zhipu", "mock"):
        return s
    return None


# --- 注册表（可根据需要扩展更多字段） ---
_REGISTRY: Dict[str, ProviderMeta] = {
    "gpt": ProviderMeta(
        key="gpt",
        label="GPT (OpenAI-compatible)",
        default_model="gpt-4o-mini",
        aliases=("openai", "chatgpt", "gpt4", "gpt-4", "gpt-4o"),
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
        notes="默认驱动，适配 /v1/chat/completions 接口。",
    ),
    "gemini": ProviderMeta(
        key="gemini",
        label="Google Gemini",
        default_model="gemini-1.5-pro-latest",
        aliases=("google",),
        api_key_env="GEMINI_API_KEY",
        base_url_env="GEMINI_BASE_URL",
        notes="generateContent API。",
    ),
    "deepseek": ProviderMeta(
        key="deepseek",
        label="DeepSeek",
        default_model="deepseek-chat",
        aliases=("deep-seek",),
        api_key_env="DEEPSEEK_API_KEY",
        base_url_env="DEEPSEEK_BASE_URL",
        notes="OpenAI 兼容 /chat/completions。",
    ),
    "zhipu": ProviderMeta(
        key="zhipu",
        label="智谱 GLM",
        default_model="glm-4",
        aliases=("zhipuai", "glm"),
        api_key_env="ZHIPU_API_KEY",
        base_url_env="ZHIPU_BASE_URL",
        notes="/api/paas/v4/chat/completions。",
    ),
    "mock": ProviderMeta(
        key="mock",
        label="Mock (开发联调)",
        default_model="mock-echo",
        aliases=("dummy", "test"),
        api_key_env=None,
        base_url_env=None,
        notes="离线/无 Key 场景回退。",
    ),
}


def has_provider(key: Optional[str]) -> bool:
    """是否存在该 Provider（key 需先 normalize）。"""
    return bool(key) and key in _REGISTRY


def get_provider_meta(key: str) -> ProviderMeta:
    """读取 Provider 元信息；若 key 无效将抛出 KeyError。"""
    return _REGISTRY[key]


def list_providers() -> List[Dict]:
    """列出所有可用 Provider 的元信息列表（字典形式）。"""
    return [m.to_dict() for m in _REGISTRY.values()]


def get_adapter_class(key: str):
    """懒加载返回适配器类，避免模块级循环依赖。
    返回类（非实例），调用方可直接 `cls(...).chat(...)`。
    """
    k = normalize_provider_key(key)
    if not k or not has_provider(k):
        raise KeyError(f"unknown provider: {key}")
    # 惰性导入
    if k == "gpt":
        from core.ai.llm.providers import GPTAdapter as C
        return C
    if k == "gemini":
        from core.ai.llm.providers import GeminiAdapter as C
        return C
    if k == "deepseek":
        from core.ai.llm.providers import DeepSeekAdapter as C
        return C
    if k == "zhipu":
        from core.ai.llm.providers import ZhipuAdapter as C
        return C
    if k == "mock":
        from core.ai.llm.providers import MockAdapter as C
        return C
    raise KeyError(f"unknown provider: {key}")

