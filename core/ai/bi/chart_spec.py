# file: core/ai/bi/chart_spec.py
# purpose: 基于字段语义给出简单图表建议（line/bar/pie）
from __future__ import annotations
from typing import Dict, List


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def suggest_spec(rows: List[dict]) -> Dict:
    if not rows:
        return {"type": "table"}
    # 取一行做字段推断
    sample = rows[0]
    keys = list(sample.keys())
    # 日期/时间字段
    time_fields = [k for k in keys if any(t in k.lower() for t in ["date", "day", "month", "time", "created_at", "biz_date"]) ]
    num_fields = [k for k in keys if _is_number(sample.get(k))]
    cat_fields = [k for k in keys if k not in num_fields]

    if time_fields and num_fields:
        x = time_fields[0]
        y = num_fields[0]
        return {"type": "line", "x": x, "y": y}
    if len(num_fields) >= 1 and len(cat_fields) >= 1:
        return {"type": "bar", "x": cat_fields[0], "y": num_fields[0]}
    if len(num_fields) == 1 and len(rows) <= 10:
        # 小计类数据可以饼图
        return {"type": "pie", "name": keys[0], "value": num_fields[0]}
    return {"type": "table"}