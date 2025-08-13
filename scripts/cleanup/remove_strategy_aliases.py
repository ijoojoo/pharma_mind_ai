# file: scripts/cleanup/remove_strategy_aliases.py
# purpose: 一次性清理旧命名残留（文件与代码引用）。默认 dry-run，仅打印计划；加 --apply 才会实际删除。
from __future__ import annotations
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 需要删除的兼容层文件（若存在则删除）
TO_DELETE = [
    PROJECT_ROOT / "core/ai/strategy/promotion.py",
    PROJECT_ROOT / "core/ai/strategy/replenishment.py",
    PROJECT_ROOT / "core/views/ai/strategy/promotion.py",
    PROJECT_ROOT / "core/views/ai/strategy/replenishment.py",
]

# 需要扫描替换/提示的旧引用（字符串级搜索）
BAD_IMPORTS = [
    "core.ai.strategy.promotion",
    "core.ai.strategy.replenishment",
    "core.views.ai.strategy.promotion",
    "core.views.ai.strategy.replenishment",
]

BAD_URL_PATTERNS = [
    "/promotion/",
    "/replenishment/",
]


def scan_repo() -> list[str]:
    hits: list[str] = []
    for p in PROJECT_ROOT.rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for needle in BAD_IMPORTS + BAD_URL_PATTERNS:
            if needle in text:
                hits.append(f"{p.relative_to(PROJECT_ROOT)}: contains '{needle}'")
                break
    return sorted(hits)


def do_delete(apply: bool = False) -> list[str]:
    msgs: list[str] = []
    for f in TO_DELETE:
        if f.exists():
            if apply:
                try:
                    f.unlink()
                    msgs.append(f"deleted: {f.relative_to(PROJECT_ROOT)}")
                except Exception as e:
                    msgs.append(f"failed to delete {f.relative_to(PROJECT_ROOT)}: {e}")
            else:
                msgs.append(f"will delete: {f.relative_to(PROJECT_ROOT)}")
        else:
            msgs.append(f"absent (ok): {f.relative_to(PROJECT_ROOT)}")
    return msgs


def main():
    apply = "--apply" in sys.argv
    print("[strategy-alias-cleanup] project=", PROJECT_ROOT)
    print("\n# 1) scanning for old imports/routes ...")
    for line in scan_repo():
        print("- ", line)
    print("\n# 2) deleting compatibility files ...")
    for line in do_delete(apply=apply):
        print("- ", line)
    if not apply:
        print("\n(dry-run) nothing has been deleted. run with --apply to perform removal.")


if __name__ == "__main__":
    main()
