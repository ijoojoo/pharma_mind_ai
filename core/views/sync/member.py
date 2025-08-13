from .base_batch import BaseBatchSyncView
from ...models import Member, Store

class MemberBatchSyncView(BaseBatchSyncView):
    model = Member
    lookup_field = 'source_member_id'
    unique_fields_for_error_handling = {'enterprise_id_card_number': 'card_number'}
    foreign_key_lookups = {'issuing_store': ('store_id', Store, 'source_store_id')}