# file: core/ai/strategy/pricing.py
# purpose: 基于成本/目标毛利/竞品价格等，给出定价建议（并返回计算明细，便于审计）
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class PricingInput:
    cost: float
    current_price: Optional[float] = None
    competitor_price: Optional[float] = None


@dataclass
class PricingConstraints:
    target_margin: float = 0.25           # 目标毛利率（25%）
    floor_margin: float = 0.05            # 最低毛利率（5%）
    ceiling_price: Optional[float] = None # 价格上限
    floor_price: Optional[float] = None   # 价格下限
    comp_weight: float = 0.4              # 与竞品锚定的权重（0~1）
    comp_delta_pct: float = -0.02         # 相对竞品的调整比例（-2% 表示略低 2%）
    round_to: float = 0.1                  # 四舍五入到 0.1 元（或 0.01 元）
    price_endings: Optional[list[float]] = None  # 价格尾数策略，如 [0.89, 0.99]


def _round_price(p: float, round_to: float, endings: Optional[list[float]] = None) -> float:
    if p <= 0:
        return 0.0
    if endings:
        # 将价格调整为最接近的“尾数”策略（仅对小数部分操作）
        import math
        integer = math.floor(p)
        frac = p - integer
        # 在 0~1 之间寻找距离最近的尾数
        tgt = min(endings, key=lambda e: abs(frac - e))
        # 若尾数 < 当前小数，且差距很大，允许进位到下一元
        if tgt < 0 or tgt >= 1:
            return round(p, 2)
        candidate = integer + tgt
        # 如果 candidate 离 p 仍很远，按 round_to 再微调
        if abs(candidate - p) > max(round_to, 0.01):
            return round(round(p / round_to) * round_to, 2)
        return round(candidate, 2)
    # 默认按 round_to 圆整
    return round(round(p / max(round_to, 0.01)) * max(round_to, 0.01), 2)


def suggest_price(product: Dict[str, Any], constraints: Dict[str, Any] | PricingConstraints) -> Dict[str, Any]:
    p = PricingInput(
        cost=float(product.get("cost", 0.0) or 0.0),
        current_price=(float(product.get("current_price")) if product.get("current_price") is not None else None),
        competitor_price=(float(product.get("competitor_price")) if product.get("competitor_price") is not None else None),
    )
    if isinstance(constraints, dict):
        c = PricingConstraints(**constraints)
    else:
        c = constraints

    # 1) 基于目标毛利率的价格
    margin_price = p.cost / max(1e-6, 1.0 - max(0.0, min(0.95, c.target_margin)))

    # 2) 基于竞品的锚定价格
    comp_price = None
    if p.competitor_price and p.competitor_price > 0:
        comp_price = p.competitor_price * (1.0 + c.comp_delta_pct)

    # 3) 融合（权重）
    if comp_price is not None:
        base = (1 - c.comp_weight) * margin_price + c.comp_weight * comp_price
    else:
        base = margin_price

    # 4) 约束（floor/ceiling & 最低毛利）
    min_by_margin = p.cost * (1.0 + max(0.0, c.floor_margin))
    floor_price = c.floor_price if c.floor_price is not None else min_by_margin
    ceiling_price = c.ceiling_price if c.ceiling_price is not None else float("inf")
    bounded = max(floor_price, min(base, ceiling_price))

    # 5) 圆整
    rounded = _round_price(bounded, c.round_to, c.price_endings)

    # 6) 结果与审计明细
    return {
        "suggested_price": float(rounded),
        "inputs": {
            "cost": p.cost,
            "current_price": p.current_price,
            "competitor_price": p.competitor_price,
        },
        "constraints": {
            "target_margin": c.target_margin,
            "floor_margin": c.floor_margin,
            "floor_price": c.floor_price,
            "ceiling_price": c.ceiling_price,
            "comp_weight": c.comp_weight,
            "comp_delta_pct": c.comp_delta_pct,
            "round_to": c.round_to,
            "price_endings": c.price_endings,
        },
        "calc": {
            "margin_price": round(margin_price, 4),
            "comp_price": (round(comp_price, 4) if comp_price is not None else None),
            "base": round(base, 4),
            "bounded": round(bounded, 4),
        },
    }
