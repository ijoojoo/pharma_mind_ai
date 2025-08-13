from .base_append_only import BaseAppendOnlySyncView
from ...models import Sale, Product, Store, Member, Employee


class SaleBatchSyncView(BaseAppendOnlySyncView):
    model = Sale
    foreign_key_lookups = {
        'product': ('product_id', Product, 'source_product_id'),
        'store': ('store_id', Store, 'source_store_id'),
        'member': ('member_id', Member, 'source_member_id'),
        'employee': ('employee_id', Employee, 'source_employee_id'),
    }