from .base_batch import BaseBatchSyncView
from ...models.product import Product

class ProductBatchSyncView(BaseBatchSyncView):
    model = Product
    lookup_field = 'source_product_id'
    unique_fields_for_error_handling = {'enterprise_id_product_code': 'product_code'}