# file: core/ai/strategy/replenish.py
# purpose: 补货策略服务（安全库存与再订货点）；基于近 N 天销量（qty）估算
from __future__ import annotations
from typing import Any, Dict, List, Tuple
from datetime import date, timedelta
from statistics import mean, pstdev
from django.db.models import Sum

try:
    from core.models import Sale, InventorySnapshot, Product  # 假定字段：Sale.qty 可选
except Exception:  # pragma: no cover
    Sale = None  # type: ignore
    InventorySnapshot = None  # type: ignore
    Product = None  # type: ignore

from core.ai.tools.inventory_tool import calc_safety_stock, calc_reorder_point


def _daily_qty_series(tenant_id: str, product_ids: List[Any], days: int) -> Dict[Any, List[float]]:
    """拉取近 days 天每天的销量数量（若无 qty 字段则回落到 0）。"""
    if Sale is None or not product_ids:
        return {}
    end = date.today()
    start = end - timedelta(days=max(1, int(days)))
    qs = (Sale.objects
          .filter(tenant_id=tenant_id, biz_date__gte=start, biz_date__lte=end, product_id__in=product_ids)
          .values("biz_date", "product_id").annotate(qty=Sum("qty")))
    # 构造日期索引
    days_list = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    ser: Dict[Any, Dict[date, float]] = {}
    for r in qs:
        pid = r["product_id"]
        ser.setdefault(pid, {})[r["biz_date"]] = float(r.get("qty") or 0.0)
    out: Dict[Any, List[float]] = {}
    for pid in product_ids:
        out[pid] = [ser.get(pid, {}).get(d, 0.0) for d in days_list]
    return out


def _latest_inventory(tenant_id: str, product_ids: List[Any]) -> Dict[Any, float]:
    """取一批 SKU 的最近库存数。"""
    if InventorySnapshot is None or not product_ids:
        return {}
    qs = (InventorySnapshot.objects
          .filter(tenant_id=tenant_id, product_id__in=product_ids)
          .values("product_id", "snapshot_time", "qty")
          .order_by("product_id", "-snapshot_time"))
    seen = set()
    out: Dict[Any, float] = {}
    for r in qs:
        pid = r["product_id"]
        if pid in seen:
            continue
        seen.add(pid)
        out[pid] = float(r.get("qty") or 0.0)
    return out


def suggest_replenishment(*, tenant_id: str, product_ids: List[Any], lookback_days: int = 28, leadtime_days: float = 7.0,
                          service_level: float = 0.95) -> List[Dict[str, Any]]:
    """给出补货建议（包含安全库存/再订货点与当前状态）。"""
    series = _daily_qty_series(tenant_id, product_ids, lookback_days)
    inv = _latest_inventory(tenant_id, product_ids)

    res: List[Dict[str, Any]] = []
    for pid in product_ids:
        qty_list = series.get(pid, [])
        if qty_list:
            d_mean = float(mean(qty_list))
            d_sigma = float(pstdev(qty_list)) if len(qty_list) > 1 else 0.0
        else:
            d_mean = 0.0
            d_sigma = 0.0
        ss = calc_safety_stock(d_sigma, leadtime_days, service_level=service_level)
        rop = calc_reorder_point(d_mean, leadtime_days, ss)
        on_hand = float(inv.get(pid, 0.0))
        need = max(0.0, rop - on_hand)
        res.append({
            "product_id": pid,
            "daily_mean": round(d_mean, 4),
            "daily_sigma": round(d_sigma, 4),
            "safety_stock": round(ss, 2),
            "reorder_point": round(rop, 2),
            "on_hand": round(on_hand, 2),
            "suggest_qty": round(need, 0),
        })
    return res