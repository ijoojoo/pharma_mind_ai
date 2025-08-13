# file: core/ai/strategy/price.py
# purpose: 定价策略服务（基于目标毛利/价格带/弹性估计给出建议价）；尽量使用 ORM 数据，缺失字段时降级处理
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from datetime import date, timedelta
from django.db.models import Sum, Count

try:
    # 业务域模型（若不存在某些字段，将在逻辑中回退）
    from core.models import Sale, Product  # 假定字段：Sale(tenant_id,biz_date,product_id,qty,total_amount) Product(id,price,cost?)
except Exception:  # pragma: no cover
    Sale = None  # type: ignore
    Product = None  # type: ignore


@dataclass
class PriceBound:
    """单品的价格带限制。"""
    min_price: Optional[float] = None  # 最低价（可空）
    max_price: Optional[float] = None  # 最高价（可空）


@dataclass
class PriceSuggestion:
    """单品的定价建议（含依据）。"""
    product_id: Any
    current_price: Optional[float]
    suggested_price: Optional[float]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# -------- 基础统计工具 --------

def _recent_sales(tenant_id: str, days: int = 28) -> Dict[Any, Dict[str, float]]:
    """读取近 days 天的按商品销量汇总（金额/数量）。缺少 qty 时仅统计 amount。"""
    if Sale is None:
        return {}
    end = date.today()
    start = end - timedelta(days=max(1, int(days)))
    qs = (Sale.objects
           .filter(tenant_id=tenant_id, biz_date__gte=start, biz_date__lte=end)
           .values("product_id")
           .annotate(amount=Sum("total_amount")))
    out: Dict[Any, Dict[str, float]] = {r["product_id"]: {"amount": float(r.get("amount") or 0.0)} for r in qs}
    # 尝试聚合数量
    try:
        qs_qty = (Sale.objects
                  .filter(tenant_id=tenant_id, biz_date__gte=start, biz_date__lte=end)
                  .values("product_id").annotate(qty=Sum("qty")))
        for r in qs_qty:
            out.setdefault(r["product_id"], {"amount": 0.0})["qty"] = float(r.get("qty") or 0.0)
    except Exception:
        # 无 qty 字段则跳过
        pass
    return out


def _product_prices(product_ids: List[Any]) -> Dict[Any, Dict[str, Optional[float]]]:
    """批量读取商品现价/成本（若缺失 cost 字段则仅返回 price）。"""
    if Product is None or not product_ids:
        return {}
    rows = list(Product.objects.filter(id__in=product_ids).values("id", "price"))
    out: Dict[Any, Dict[str, Optional[float]]] = {r["id"]: {"price": float(r.get("price") or 0.0), "cost": None} for r in rows}
    # 可选成本
    try:
        rows2 = list(Product.objects.filter(id__in=product_ids).values("id", "cost"))
        for r in rows2:
            if r.get("id") in out:
                out[r["id"]]["cost"] = (float(r.get("cost")) if r.get("cost") is not None else None)
            else:
                out[r["id"]] = {"price": None, "cost": (float(r.get("cost")) if r.get("cost") is not None else None)}
    except Exception:
        pass
    return out


# -------- 定价算法主流程 --------

def suggest_prices(*, tenant_id: str, items: List[Dict[str, Any]], target_margin: Optional[float] = None,
                   bounds: Dict[Any, PriceBound] | None = None) -> List[Dict[str, Any]]:
    """对一批商品给出定价建议。
    参数：
      - items: [{"product_id":X, "current_price"?, "cost"?}]，若未提供则从 Product 拉取。
      - target_margin: 目标毛利率（0-1），若提供且有 cost 将按毛利率计算建议价。
      - bounds: 价格带约束（每个 product_id 可设置 min/max）。
    回参：[{product_id,current_price,cost?,suggested_price,reason}]
    """
    product_ids = [it.get("product_id") for it in items if it.get("product_id") is not None]
    price_map = _product_prices(product_ids)
    sales_map = _recent_sales(tenant_id)

    res: List[Dict[str, Any]] = []
    for it in items:
        pid = it.get("product_id")
        cur_price = it.get("current_price")
        cost = it.get("cost")
        meta = price_map.get(pid, {})
        if cur_price is None:
            cur_price = meta.get("price")
        if cost is None:
            cost = meta.get("cost")
        # 基于目标毛利率
        reason_parts: List[str] = []
        suggested: Optional[float] = None
        if target_margin is not None and cost is not None:
            try:
                m = max(0.0, min(0.99, float(target_margin)))
                suggested = round(float(cost) / (1.0 - m), 2)
                reason_parts.append(f"按目标毛利率 {m:.0%} 计算")
            except Exception:
                suggested = None
        # 基于销量弹性（启发式：销量越低越倾向于下调 5-10%）
        if suggested is None and cur_price is not None:
            stat = sales_map.get(pid) or {}
            qty = float(stat.get("qty") or 0.0)
            amount = float(stat.get("amount") or 0.0)
            if qty <= 0 and amount <= 0:
                # 无数据：保持现价
                suggested = float(cur_price)
                reason_parts.append("缺少销量数据，保持现价")
            else:
                # 简单启发：低销量则降 5%，高销量则微升 2%
                adj = -0.05 if qty < 5 else (0.02 if qty > 50 else 0.0)
                suggested = round(float(cur_price) * (1.0 + adj), 2)
                reason_parts.append(f"基于近销启发式调整{adj:+.0%}")
        # 约束价格带
        if bounds and pid in bounds and suggested is not None:
            b = bounds[pid]
            if b.min_price is not None and suggested < b.min_price:
                suggested = float(b.min_price)
                reason_parts.append("触底到最小价")
            if b.max_price is not None and suggested > b.max_price:
                suggested = float(b.max_price)
                reason_parts.append("封顶到最大价")
        res.append(PriceSuggestion(product_id=pid, current_price=(None if cur_price is None else float(cur_price)),
                                   suggested_price=suggested, reason="; ".join(reason_parts) or "-"
                                   ).to_dict())
    return res
