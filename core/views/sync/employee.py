from .base_batch import BaseBatchSyncView
from ...models import Employee, Store


class EmployeeBatchSyncView(BaseBatchSyncView):
    model = Employee
    lookup_field = 'source_employee_id'
    unique_fields_for_error_handling = {'enterprise_id_employee_number': 'employee_number'}
    foreign_key_lookups = {'store': ('store_id', Store, 'source_store_id')}