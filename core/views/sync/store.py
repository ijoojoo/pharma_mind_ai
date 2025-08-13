from .base_batch import BaseBatchSyncView
from ...models import Store


class StoreBatchSyncView(BaseBatchSyncView):
    model = Store
    lookup_field = 'source_store_id'
    unique_fields_for_error_handling = {'enterprise_id_name': 'name'}