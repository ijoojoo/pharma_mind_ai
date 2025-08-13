from .base_append_only import BaseAppendOnlySyncView
from ...models import InventorySnapshot, Store, Product


class InventorySnapshotBatchSyncView(BaseAppendOnlySyncView):
    model = InventorySnapshot
    foreign_key_lookups = {
        'product': ('product_id', Product, 'source_product_id'),
        'store': ('store_id', Store, 'source_store_id'),
    }