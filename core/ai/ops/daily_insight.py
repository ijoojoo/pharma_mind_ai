# file: core/ai/ops/daily_insight.py
# purpose: 读取销售/库存等基础数据并输出结构化洞察（MVP：仅聚合基础指标）
from __future__ import annotations
from datetime import date, timedelta
from typing import Optional, Dict, Any
from django.db.models import Sum
from core.models import Sale, InventorySnapshot


def compute_daily_metrics(*, target_date: Optional[date] = None, store_ids: Optional[list[int]] = None) -> Dict[str, Any]:
    d = target_date or date.today()
    qs = Sale.objects.filter(biz_date=d)
    if store_ids:
        qs = qs.filter(store_id__in=store_ids)
    sales = qs.aggregate(amount=Sum("total_amount"))[["amount"]] if False else qs.aggregate(amount=Sum("total_amount"))
    # 库存（取最近一天快照求和）
    inv = InventorySnapshot.objects.order_by("-snapshot_time")
    if store_ids:
        inv = inv.filter(store_id__in=store_ids)
    # 仅示例：聚合总库存数量
    inv_qty = inv.values_list("qty", flat=True)[:1000]
    total_inv_qty = sum([x or 0 for x in inv_qty])
    return {"date": d, "sales_amount": float(sales.get("amount") or 0), "inventory_qty": float(total_inv_qty)}

