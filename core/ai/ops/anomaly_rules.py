# file: core/ai/ops/anomaly_rules.py
# purpose: 异常检测规则实现（销量骤降、缺货、价格异常）；统一 detect_anomalies 入口
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple
from django.db.models import Sum

# 这些模型来自你的业务域（在日结里已用过）
from core.models import Sale, InventorySnapshot  # 假定存在以下字段：见各函数注释


@dataclass
class Rule:
    id: str
    type: str  # "sales_drop" | "stockout" | "price_spike"
    threshold_pct: Optional[float] = None  # 百分比阈值，例如 30 表示 30%
    min_qty: Optional[float] = None  # 缺货阈值（<= 视为异常）
    lookback: int = 7  # 滑动窗口天数（不含最后一天）
    group_by: Tuple[str, ...] = ("store_id", "product_id")


# --------- 时间工具 ---------

def _to_date(v: Any) -> date:
    if isinstance(v, date):
        return v
    return datetime.fromisoformat(str(v)).date()


# --------- 数据读取 ---------

def fetch_sales_daily(*, tenant_id: str, start: date, end: date, group_by: Iterable[str]) -> List[dict]:
    """
    读取销量按天聚合的数据。
    需求字段（Sale）：biz_date(date), total_amount(decimal/float), 可选 qty/quantity(int/decimal), 以及分组字段（如 store_id/product_id）。
    返回：[{biz_date, <group_by...>, amount, qty?}]
    """
    gb = ["biz_date", *list(group_by)]
    qs = Sale.objects.filter(tenant_id=tenant_id, biz_date__gte=start, biz_date__lte=end)
    # 总金额
    qs = qs.values(*gb).annotate(amount=Sum("total_amount"))
    rows: List[dict] = list(qs)
    # 尝试同时取数量（若无该字段则忽略）
    try:
        qs2 = Sale.objects.filter(tenant_id=tenant_id, biz_date__gte=start, biz_date__lte=end).values(*gb).annotate(qty=Sum("qty"))
        qty_map = {tuple([r[g] for g in gb]): r.get("qty") for r in qs2}
        for r in rows:
            key = tuple([r[g] for g in gb])
            r["qty"] = qty_map.get(key)
    except Exception:
        # 无 qty 字段
        for r in rows:
            r["qty"] = None
    return rows


def fetch_latest_inventory(*, tenant_id: str, as_of: date, group_by: Iterable[str]) -> List[dict]:
    """
    获取某日（含）之前的最近一次库存快照。
    需求字段（InventorySnapshot）：snapshot_time(datetime/date), qty(numeric)，以及分组字段（store_id/product_id）。
    采用内存去重，避免数据库方言差异（distinct on）。
    返回：[{<group_by...>, qty}]
    """
    gb = list(group_by)
    qs = (
        InventorySnapshot.objects.filter(tenant_id=tenant_id, snapshot_time__date__lte=as_of)
        .values(*gb, "snapshot_time", "qty")
        .order_by("-snapshot_time")
    )
    seen = set()
    out: List[dict] = []
    for r in qs:
        key = tuple(r[g] for g in gb)
        if key in seen:
            continue
        seen.add(key)
        out.append({**{g: r[g] for g in gb}, "qty": r.get("qty")})
        if len(out) >= 5000:
            break  # 简单上限，避免一次拉太多
    return out


# --------- 规则实现 ---------

def _group_key(rec: dict, group_by: Iterable[str]) -> tuple:
    return tuple(rec.get(g) for g in group_by)


def detect_sales_drop(*, tenant_id: str, start: date, end: date, rule: Rule) -> List[dict]:
    rows = fetch_sales_daily(tenant_id=tenant_id, start=start, end=end, group_by=rule.group_by)
    # 按 group_by 分桶
    buckets: Dict[tuple, Dict[date, dict]] = defaultdict(dict)
    for r in rows:
        buckets[_group_key(r, rule.group_by)][r["biz_date"]] = r
    last_day = end
    res: List[dict] = []
    for gk, series in buckets.items():
        # 最近一天
        last = series.get(last_day)
        if not last:
            continue
        # 回看窗口（不含最后一天）
        lb_days = [last_day - timedelta(days=i) for i in range(1, rule.lookback + 1)]
        base_vals = [series[d]["amount"] for d in lb_days if d in series]
        if len(base_vals) < max(3, rule.lookback // 2):
            continue  # 样本不足
        base_avg = (sum(float(x or 0.0) for x in base_vals) / len(base_vals)) if base_vals else 0.0
        today_amt = float(last.get("amount") or 0.0)
        if base_avg <= 0:
            continue
        drop_pct = max(0.0, (base_avg - today_amt) / base_avg * 100.0)
        if drop_pct >= float(rule.threshold_pct or 30.0):
            res.append({
                "rule_id": rule.id,
                "type": rule.type,
                "group": dict(zip(rule.group_by, gk)),
                "base_avg": round(base_avg, 2),
                "today": round(today_amt, 2),
                "drop_pct": round(drop_pct, 2),
                "severity": "high" if drop_pct >= 50 else "medium",
            })
    return res


def detect_stockout(*, tenant_id: str, as_of: date, rule: Rule) -> List[dict]:
    rows = fetch_latest_inventory(tenant_id=tenant_id, as_of=as_of, group_by=rule.group_by)
    threshold = float(rule.min_qty if rule.min_qty is not None else 0.0)
    res: List[dict] = []
    for r in rows:
        qty = float(r.get("qty") or 0.0)
        if qty <= threshold:
            res.append({
                "rule_id": rule.id,
                "type": rule.type,
                "group": {k: r.get(k) for k in rule.group_by},
                "qty": qty,
                "threshold": threshold,
                "severity": "high" if qty <= 0 else "medium",
            })
    return res


def detect_price_spike(*, tenant_id: str, start: date, end: date, rule: Rule) -> List[dict]:
    rows = fetch_sales_daily(tenant_id=tenant_id, start=start, end=end, group_by=rule.group_by)
    buckets: Dict[tuple, Dict[date, dict]] = defaultdict(dict)
    for r in rows:
        buckets[_group_key(r, rule.group_by)][r["biz_date"]] = r
    res: List[dict] = []
    for gk, series in buckets.items():
        last = series.get(end)
        if not last:
            continue
        # 需要 qty 支持
        if not last.get("qty"):
            continue
        lb_days = [end - timedelta(days=i) for i in range(1, rule.lookback + 1)]
        base_unit_prices = []
        for d in lb_days:
            rec = series.get(d)
            if not rec:
                continue
            amt = float(rec.get("amount") or 0.0)
            qty = float(rec.get("qty") or 0.0)
            if qty <= 0:
                continue
            base_unit_prices.append(amt / qty)
        if len(base_unit_prices) < max(3, rule.lookback // 2):
            continue
        base_avg_price = sum(base_unit_prices) / len(base_unit_prices)
        today_amt = float(last.get("amount") or 0.0)
        today_qty = float(last.get("qty") or 0.0)
        if today_qty <= 0 or base_avg_price <= 0:
            continue
        today_price = today_amt / today_qty
        diff_pct = abs(today_price - base_avg_price) / base_avg_price * 100.0
        if diff_pct >= float(rule.threshold_pct or 25.0):
            res.append({
                "rule_id": rule.id,
                "type": rule.type,
                "group": dict(zip(rule.group_by, gk)),
                "base_avg_price": round(base_avg_price, 4),
                "today_price": round(today_price, 4),
                "diff_pct": round(diff_pct, 2),
                "severity": "high" if diff_pct >= 50 else "medium",
            })
    return res


def detect_anomalies(*, tenant_id: str, window: dict, rules: List[dict]) -> List[dict]:
    start = _to_date(window.get("start")) if window.get("start") else (date.today() - timedelta(days=14))
    end = _to_date(window.get("end")) if window.get("end") else date.today()
    out: List[dict] = []
    for rd in rules or []:
        rule = Rule(
            id=str(rd.get("id") or rd.get("type")),
            type=str(rd.get("type")),
            threshold_pct=rd.get("threshold_pct"),
            min_qty=rd.get("min_qty"),
            lookback=int(rd.get("lookback", 7)),
            group_by=tuple(rd.get("group_by") or ("store_id", "product_id")),
        )
        if rule.type == "sales_drop":
            out.extend(detect_sales_drop(tenant_id=tenant_id, start=start, end=end, rule=rule))
        elif rule.type == "stockout":
            out.extend(detect_stockout(tenant_id=tenant_id, as_of=end, rule=rule))
        elif rule.type == "price_spike":
            out.extend(detect_price_spike(tenant_id=tenant_id, start=start, end=end, rule=rule))
    # 统一排序：高严重度优先
    out.sort(key=lambda x: (0 if x.get("severity") == "high" else 1, x.get("type"), str(x.get("group"))))
    return out