# file: core/ai/strategy/promo.py
# purpose: 促销策略服务（挑选候选 SKU 与促销力度建议）；基于销量骤降与库存情况的简单启发
from __future__ import annotations
from typing import Any, Dict, List
from datetime import date, timedelta
from django.db.models import Sum

try:
    from core.models import Sale, InventorySnapshot, Product  # 假定字段：见下文注释
except Exception:  # pragma: no cover
    Sale = None  # type: ignore
    InventorySnapshot = None  # type: ignore
    Product = None  # type: ignore


def suggest_promotions(*, tenant_id: str, top_k: int = 20, lookback: int = 14) -> List[Dict[str, Any]]:
    """返回促销候选（销量下滑且库存较高）。"""
    if Sale is None or InventorySnapshot is None:
        return []
    end = date.today()
    mid = end - timedelta(days=max(3, lookback // 2))
    start = end - timedelta(days=lookback)
    # 近半窗口销量
    recent = (Sale.objects
              .filter(tenant_id=tenant_id, biz_date__gt=mid, biz_date__lte=end)
              .values("product_id").annotate(amount=Sum("total_amount")))
    recent_map = {r["product_id"]: float(r.get("amount") or 0.0) for r in recent}
    # 前半窗口基线
    base = (Sale.objects
            .filter(tenant_id=tenant_id, biz_date__gte=start, biz_date__lte=mid)
            .values("product_id").annotate(amount=Sum("total_amount")))
    base_map = {r["product_id"]: float(r.get("amount") or 0.0) for r in base}

    # 库存：取最近快照
    inv_map: Dict[Any, float] = {}
    try:
        qs = (InventorySnapshot.objects
              .filter(tenant_id=tenant_id)
              .values("product_id", "snapshot_time", "qty")
              .order_by("product_id", "-snapshot_time"))
        seen = set()
        for r in qs:
            pid = r["product_id"]
            if pid in seen:
                continue
            seen.add(pid)
            inv_map[pid] = float(r.get("qty") or 0.0)
    except Exception:
        pass

    # 组装候选
    cand: List[Dict[str, Any]] = []
    for pid, base_amt in base_map.items():
        cur = recent_map.get(pid, 0.0)
        drop = (base_amt - cur)
        drop_pct = (drop / base_amt * 100.0) if base_amt > 0 else 0.0
        if drop_pct >= 25.0 and inv_map.get(pid, 0.0) > 0:
            cand.append({"product_id": pid, "drop_pct": round(drop_pct, 2), "inventory": inv_map.get(pid, 0.0)})
    # 选 top_k
    cand.sort(key=lambda x: x["drop_pct"], reverse=True)
    out = cand[: max(1, min(top_k, 100))]

    # 可选：附上建议折扣（简单按下滑幅度映射）
    for it in out:
        pct = it["drop_pct"]
        if pct >= 60:
            it["suggest_discount"] = 0.2
        elif pct >= 40:
            it["suggest_discount"] = 0.15
        else:
            it["suggest_discount"] = 0.1
    return out