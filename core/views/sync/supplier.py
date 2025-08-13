from .base_batch import BaseBatchSyncView
from ...models import Supplier


class SupplierBatchSyncView(BaseBatchSyncView):
    model = Supplier
    lookup_field = 'source_supplier_id'
    unique_fields_for_error_handling = {'enterprise_id_supplier_code': 'supplier_code'}