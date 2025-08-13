from .base_append_only import BaseAppendOnlySyncView
from ...models import Purchase, Purchase, Supplier


class PurchaseBatchSyncView(BaseAppendOnlySyncView):
    model = Purchase
    foreign_key_lookups = {
        'product': ('product_id', Purchase, 'source_product_id'),
        'supplier': ('supplier_id', Supplier, 'source_supplier_id'),
    }