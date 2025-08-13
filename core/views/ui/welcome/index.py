# core/views/welcome/index.py
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Tuple

from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce, ExtractHour, TruncDate
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Sale, Store
from core.views.utils import (
    get_enterprise,
    get_date_range_from_request,
    is_range_mode,
    hour_labels,
    ok,
    bad_request,
)

# ============ 公共汇总工具 ============

def _profit_expr():
    """优先用 gross_profit_amount；没有就用 total_amount - total_cost_amount。"""
    return Coalesce(
        F("gross_profit_amount"),
        ExpressionWrapper(
            Coalesce(F("total_amount"), Decimal(0)) - Coalesce(F("total_cost_amount"), Decimal(0)),
            output_field=DecimalField(max_digits=18, decimal_places=4),
        ),
    )


def _sum_amount(qs):
    return qs.aggregate(v=Coalesce(Sum("total_amount"), Decimal(0)))["v"] or Decimal(0)


def _sum_profit(qs):
    return qs.aggregate(v=Coalesce(Sum(_profit_expr()), Decimal(0)))["v"] or Decimal(0)


def _count_traffic(qs):
    # 以 source_sale_id 代表一次交易，做去重
    return qs.values("source_sale_id").distinct().count()


# ============ 1) 顶部 KPI（今日）===========

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def kpi_today(request):
    """
    返回：
    {
      "amount": {"value": number, "target": number, "hb": number, "yb": number},
      "profit": {"value": number, "target": number, "hb": number, "yb": number},
      "traffic": {"value": number, "target": number, "hb": number, "yb": number},
      "member": {"value": number, "target": number, "hb": number, "yb": number}
    }
    """
    enterprise = get_enterprise(request)
    if not enterprise:
        return bad_request("未识别到企业（X-Enterprise-ID 或用户默认企业）")

    today = timezone.localdate()
    yesterday = today - timezone.timedelta(days=1)
    last_week_same_day = today - timezone.timedelta(days=7)

    base = Sale.objects.filter(enterprise=enterprise)
    qs_today = base.filter(sale_time__date=today)
    qs_yesterday = base.filter(sale_time__date=yesterday)
    qs_lastweek = base.filter(sale_time__date=last_week_same_day)

    # 销售额
    amt_today = _sum_amount(qs_today)
    amt_yest = _sum_amount(qs_yesterday)
    amt_lastwk = _sum_amount(qs_lastweek)

    # 毛利额
    profit_today = _sum_profit(qs_today)
    profit_yest = _sum_profit(qs_yesterday)
    profit_lastwk = _sum_profit(qs_lastweek)

    # 客流
    traffic_today = _count_traffic(qs_today)
    traffic_yest = _count_traffic(qs_yesterday)
    traffic_lastwk = _count_traffic(qs_lastweek)

    def _ratio(cur, base):
        base = float(base or 0)
        if base <= 0:
            return 0.0
        return float(cur) / base - 1.0

    # 目标：简易基线 -> 最近7日（不含今日）的日均 * 1.05
    last7 = base.filter(sale_time__date__gte=today - timezone.timedelta(days=7),
                        sale_time__date__lt=today)
    days_7 = 7.0
    amt_target = float(_sum_amount(last7)) / days_7 * 1.05
    profit_target = float(_sum_profit(last7)) / days_7 * 1.05
    traffic_target = float(_count_traffic(last7)) / days_7 * 1.05

    # 会员：如果 models.profiles.Member 存在且有 created_at，用它统计
    try:
        from core.models import Member
        mem_today = Member.objects.filter(enterprise=enterprise, created_at__date=today).count()
        mem_yest = Member.objects.filter(enterprise=enterprise, created_at__date=yesterday).count()
        mem_lastwk = Member.objects.filter(enterprise=enterprise, created_at__date=last_week_same_day).count()
        last7_mem = Member.objects.filter(
            enterprise=enterprise,
            created_at__date__gte=today - timezone.timedelta(days=7),
            created_at__date__lt=today,
        ).count()
        mem_target = float(last7_mem) / days_7 * 1.05
    except Exception:
        mem_today = mem_yest = mem_lastwk = 0
        mem_target = 0.0

    data = {
        "amount": {
            "value": float(amt_today),
            "target": round(amt_target, 2),
            "hb": _ratio(amt_today, amt_yest),
            "yb": _ratio(amt_today, amt_lastwk),
        },
        "profit": {
            "value": float(profit_today),
            "target": round(profit_target, 2),
            "hb": _ratio(profit_today, profit_yest),
            "yb": _ratio(profit_today, profit_lastwk),
        },
        "traffic": {
            "value": float(traffic_today),
            "target": round(traffic_target, 2),
            "hb": _ratio(traffic_today, traffic_yest),
            "yb": _ratio(traffic_today, traffic_lastwk),
        },
        "member": {
            "value": float(mem_today),
            "target": round(mem_target, 2),
            "hb": _ratio(mem_today, mem_yest),
            "yb": _ratio(mem_today, mem_lastwk),
        },
    }
    return ok(data)


# ============ 2) 今日分时 ===========

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_today_hourly(request):
    """
    返回：
    {
      "hours": ["8:00", ..., "22:00"],
      "sales": number[],
      "traffic": number[],
      "profit": number[]
    }
    """
    enterprise = get_enterprise(request)
    if not enterprise:
        return bad_request("未识别到企业（X-Enterprise-ID 或用户默认企业）")

    today = timezone.localdate()
    base = Sale.objects.filter(enterprise=enterprise, sale_time__date=today)

    rows = (
        base
        .annotate(h=ExtractHour("sale_time"))
        .values("h")
        .annotate(
            sales=Coalesce(Sum("total_amount"), Decimal(0)),
            profit=Coalesce(Sum(_profit_expr()), Decimal(0)),
            traffic=Count("source_sale_id", distinct=True),
        )
    )

    label = hour_labels(8, 22)
    sales = [0.0 for _ in label]
    profit = [0.0 for _ in label]
    traffic = [0.0 for _ in label]

    idx = {int(h.split(":")[0]): i for i, h in enumerate(label)}

    for r in rows:
        h = int(r["h"] or 0)
        if 8 <= h <= 22 and h in idx:
            i = idx[h]
            sales[i] = float(r["sales"] or 0)
            profit[i] = float(r["profit"] or 0)
            traffic[i] = float(r["traffic"] or 0)

    return ok({
        "hours": label,
        "sales": sales,
        "profit": profit,
        "traffic": traffic,
    })


# ============ 3) 近7日指标 ===========

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sales_seven_days(request):
    """
    Query: ?metric=amount|profit|traffic
    返回：
    {
      "dates": ["MM/DD", ... x7],
      "values": number[],
      "avgTicket": number[]
    }
    """
    enterprise = get_enterprise(request)
    if not enterprise:
        return bad_request("未识别到企业（X-Enterprise-ID 或用户默认企业）")

    metric = (request.query_params.get("metric") or "amount").lower()
    if metric not in ("amount", "profit", "traffic"):
        return bad_request("metric 仅支持 amount/profit/traffic")

    today = timezone.localdate()
    start = today - timezone.timedelta(days=6)

    base = Sale.objects.filter(enterprise=enterprise, sale_time__date__gte=start, sale_time__date__lte=today)

    # 每日销售额 / 毛利 / 客流
    per_day = (
        base
        .annotate(d=TruncDate("sale_time"))
        .values("d")
        .annotate(
            amount=Coalesce(Sum("total_amount"), Decimal(0)),
            profit=Coalesce(Sum(_profit_expr()), Decimal(0)),
            traffic=Count("source_sale_id", distinct=True),
            qty=Coalesce(Sum("quantity"), Decimal(0)),
        )
    )
    day_map: Dict[str, Dict[str, float]] = {}
    for r in per_day:
        d = r["d"].strftime("%m/%d")
        day_map[d] = {
            "amount": float(r["amount"] or 0),
            "profit": float(r["profit"] or 0),
            "traffic": float(r["traffic"] or 0),
            "qty": float(r["qty"] or 0),
        }

    dates: List[str] = []
    values: List[float] = []
    avg_ticket: List[float] = []

    cur = start
    while cur <= today:
        key = cur.strftime("%m/%d")
        dates.append(key)
        row = day_map.get(key, {"amount": 0, "profit": 0, "traffic": 0, "qty": 0})
        values.append(float(row[metric]))
        # 平均客单价：销售额 / 客流
        traffic = row.get("traffic", 0) or 0
        avg_ticket.append(round((row.get("amount", 0) / traffic) if traffic else 0.0, 2))
        cur += timezone.timedelta(days=1)

    return ok({
        "dates": dates,
        "values": values,
        "avgTicket": avg_ticket,
    })


# ============ 4) 各门店 KPI 完成度 vs 时间进度 ===========

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def kpi_stores_progress(request):
    """
    Query:
      - mode=daily|range
      - start=YYYY-MM-DD
      - end=YYYY-MM-DD
    返回：
      [
        {"store":"门店A","target":number,"current":number,"type":"daily"|"range","start"?:str,"end"?:str}
      ]
    """
    enterprise = get_enterprise(request)
    if not enterprise:
        return bad_request("未识别到企业（X-Enterprise-ID 或用户默认企业）")

    range_mode = is_range_mode(request)  # mode=range
    if range_mode:
        sd, ed = get_date_range_from_request(request, default="last7")
    else:
        today = timezone.localdate()
        sd, ed = today, today

    q = Sale.objects.filter(enterprise=enterprise, sale_time__date__gte=sd, sale_time__date__lte=ed)
    per_store = (
        q.values("store_id", "store__name")
        .annotate(current=Coalesce(Sum("total_amount"), Decimal(0)))
    )

    # 目标：使用「区间外的最近7天日均 * 区间天数 * 1.05」做基线
    days = (ed - sd).days + 1
    last7_base = Sale.objects.filter(
        enterprise=enterprise,
        sale_time__date__gte=sd - timezone.timedelta(days=7),
        sale_time__date__lt=sd,
    ).values("store_id").annotate(hist=Coalesce(Sum("total_amount"), Decimal(0)))
    last7_map = {r["store_id"]: float(r["hist"] or 0) for r in last7_base}

    data = []
    for r in per_store:
        store_name = r["store__name"] or "-"
        cur_val = float(r["current"] or 0)
        hist7 = last7_map.get(r["store_id"], 0.0)
        target = (hist7 / 7.0) * days * 1.05 if hist7 > 0 else max(cur_val, 1.0) * 1.1  # 没历史时给轻微上浮目标
        item = {
            "store": store_name,
            "target": round(float(target), 2),
            "current": round(cur_val, 2),
            "type": "range" if range_mode else "daily",
        }
        if range_mode:
            item.update({"start": sd.strftime("%Y-%m-%d"), "end": ed.strftime("%Y-%m-%d")})
        data.append(item)

    # 为了前端“龙虎榜”先取前 10
    data.sort(key=lambda x: x["current"], reverse=True)
    return ok(data[:10])


# ============ 5) AI 复盘（简单可用版） ===========

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ai_dashboard_review(request):
    """
    Body: { "role": "director"|"manager", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }
    返回：
    {
      "summary": {
        "totalSales": "¥xxx,xxx",
        "peakHour": "18:00",
        "bestStore": "门店D",
        "avgCompletion": 0.76,
        "timeProgress": 0.71
      },
      "highlights": [...],
      "risks": [...],
      "actions": [...]
    }
    """
    enterprise = get_enterprise(request)
    if not enterprise:
        return bad_request("未识别到企业（X-Enterprise-ID 或用户默认企业）")

    role = (request.data.get("role") or "director").lower()
    sd, ed = get_date_range_from_request(request, default="last7")

    base = Sale.objects.filter(enterprise=enterprise, sale_time__date__gte=sd, sale_time__date__lte=ed)

    # 总销售额
    total_sales = float(_sum_amount(base))

    # 峰值小时
    hour_rows = (
        base.annotate(h=ExtractHour("sale_time"))
            .values("h")
            .annotate(sales=Coalesce(Sum("total_amount"), Decimal(0)))
    )
    if hour_rows:
        peak_hour = max(hour_rows, key=lambda r: float(r["sales"] or 0)).get("h") or 0
    else:
        peak_hour = 0

    # 最佳门店
    store_rows = (
        base.values("store__name")
            .annotate(sales=Coalesce(Sum("total_amount"), Decimal(0)))
    )
    best_store = store_rows and max(store_rows, key=lambda r: float(r["sales"] or 0)).get("store__name") or "-"

    # 完成度与时间进度
    # ——— 当前值与目标（同 kpi_stores_progress 的逻辑）———
    days = (ed - sd).days + 1
    last7 = Sale.objects.filter(
        enterprise=enterprise,
        sale_time__date__gte=sd - timezone.timedelta(days=7),
        sale_time__date__lt=sd,
    ).values("store_id").annotate(hist=Coalesce(Sum("total_amount"), Decimal(0)))
    last7_map = {r["store_id"]: float(r["hist"] or 0) for r in last7}
    cur_rows = base.values("store_id").annotate(cur=Coalesce(Sum("total_amount"), Decimal(0)))
    rates = []
    for r in cur_rows:
        cur = float(r["cur"] or 0)
        hist7 = last7_map.get(r["store_id"], 0.0)
        target = (hist7 / 7.0) * days * 1.05 if hist7 > 0 else max(cur, 1.0) * 1.1
        rate = (cur / target) if target > 0 else 0.0
        rates.append(rate)
    avg_completion = sum(rates) / len(rates) if rates else 0.0

    # 时间进度（以日为单位）
    def _time_progress(sd, ed):
        today = timezone.localdate()
        if today <= sd:
            return 0.0
        if today >= ed:
            return 1.0
        total_days = (ed - sd).days + 1
        elapsed_days = (today - sd).days + 1
        return min(1.0, max(0.0, elapsed_days / total_days))

    time_progress = _time_progress(sd, ed)

    # 一些基于简单阈值的亮点与风险
    highlights: List[str] = []
    risks: List[str] = []
    actions: List[str] = []

    if avg_completion >= 0.8:
        highlights.append("整体 KPI 完成度较高（≥80%），策略执行到位。")
    if total_sales >= 1_000_000:
        highlights.append("区间销售额破百万，贡献强劲。")

    # 风险：时间进度 > 完成度
    if avg_completion + 0.05 < time_progress:
        risks.append("KPI 完成度落后于时间进度，需加速推进。")

    # 行动建议（示例）
    if role == "director":
        actions += [
            "建议对低完成度门店进行复盘，复制高潜门店陈列与动线。",
            "对近效期 SKU 做周末引流单，叠加会员券提升转化。",
        ]
    else:
        actions += [
            "晚高峰加配 1 名导购，缩短收银等待时间。",
            "维生素等高毛利品类做搭售建议，提高客单价。",
        ]

    # 输出
    return ok({
        "summary": {
            "totalSales": f"¥{int(round(total_sales, 0)):,}",
            "peakHour": f"{int(peak_hour)}:00",
            "bestStore": best_store or "-",
            "avgCompletion": round(float(avg_completion), 4),
            "timeProgress": round(float(time_progress), 4),
        },
        "highlights": highlights,
        "risks": risks,
        "actions": actions,
    })
