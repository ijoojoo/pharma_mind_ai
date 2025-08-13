# file: core/ai/bi/schema.py
# purpose: BI 白名单配置与字段元数据
# - 向后兼容：保留 ALLOWED_VIEWS（供旧代码引用）
# - 新增：VIEW_COLUMNS（每个视图允许查询/排序的字段）与 HELP_TEXT（给 LLM 的简要字段语义）
from __future__ import annotations
from typing import Dict, List

# 仅允许读取这些只读视图；请在数据库中创建相应 VIEW，并保证行级权限（如按 tenant_id 过滤）
ALLOWED_VIEWS: Dict[str, str] = {
    "sales": "report_sales_view",
    "inventory": "report_inventory_view",
    "products": "report_products_view",
}

# 每个视图允许暴露的字段（用于列选择与排序校验）
VIEW_COLUMNS: Dict[str, List[str]] = {
    "report_sales_view": [
        "biz_date", "store_id", "product_id", "category", "amount", "qty", "unit_price",
    ],
    "report_inventory_view": [
        "snapshot_date", "store_id", "product_id", "qty", "on_way_qty",
    ],
    "report_products_view": [
        "product_id", "sku", "name", "category", "brand", "price",
    ],
}

# 给 NL2SQL/LLM 的简易帮助（可选）
HELP_TEXT: Dict[str, str] = {
    "report_sales_view": "日销量视图，包含 biz_date(日期), store_id, product_id, category, amount(金额), qty(数量), unit_price(单价)",
    "report_inventory_view": "库存快照视图，包含 snapshot_date, store_id, product_id, qty(现存量), on_way_qty(在途)",
    "report_products_view": "商品基础视图，包含 product_id, sku, name, category, brand, price",
}