from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from ..authentication import EnterpriseAPIKeyAuthentication
from ..models import (
    Product, Store, Supplier, Purchase, Sale, 
    InventorySnapshot, Member, Employee
)

class BaseSyncView(APIView):
    authentication_classes = [EnterpriseAPIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    model = None
    foreign_key_lookups = {}

    def _prepare_fk_maps(self, enterprise, data_list):
        fk_ids_to_fetch = {fk_info[1].__name__: set() for fk_info in self.foreign_key_lookups.values()}
        for data_item in data_list:
            for source_id_key, fk_model, _ in self.foreign_key_lookups.values():
                source_id = data_item.get(source_id_key)
                if source_id:
                    fk_ids_to_fetch[fk_model.__name__].add(source_id)

        fk_object_maps = {}
        for fk_model_name, source_ids in fk_ids_to_fetch.items():
            _, fk_model, fk_lookup_field = next(info for info in self.foreign_key_lookups.values() if info[1].__name__ == fk_model_name)
            queryset = fk_model.objects.filter(enterprise=enterprise, **{f"{fk_lookup_field}__in": source_ids})
            fk_object_maps[fk_model_name] = {str(getattr(obj, fk_lookup_field)): obj for obj in queryset}
        return fk_object_maps

    def _process_and_validate_data(self, enterprise, data_list, fk_object_maps):
        processed_list = []
        for data_item in data_list:
            instance_data = data_item.copy()
            instance_data['enterprise'] = enterprise
            for fk_field, (source_id_key, fk_model, _) in self.foreign_key_lookups.items():
                source_id = instance_data.pop(source_id_key, None)
                if source_id:
                    fk_map = fk_object_maps.get(fk_model.__name__, {})
                    if str(source_id) in fk_map:
                        instance_data[fk_field] = fk_map[str(source_id)]
                    else:
                        raise ValueError(f"关联数据错误：未找到 {fk_model._meta.verbose_name}，其源系统ID为 '{source_id}'。")
            processed_list.append(instance_data)
        return processed_list

class BaseBatchSyncView(BaseSyncView):
    lookup_field = None
    unique_fields_for_error_handling = {}

    def post(self, request, *args, **kwargs):
        enterprise = request.auth.enterprise
        data_list = request.data
        if not isinstance(data_list, list):
            return Response({"error": "无效的数据格式，期望一个JSON数组"}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        updated_count = 0
        current_item_for_error_reporting = {}
        
        try:
            fk_object_maps = self._prepare_fk_maps(enterprise, data_list)
            processed_data_list = self._process_and_validate_data(enterprise, data_list, fk_object_maps)

            with transaction.atomic():
                for i, instance_data in enumerate(processed_data_list):
                    current_item_for_error_reporting = data_list[i]
                    
                    lookup_kwargs = {'enterprise': enterprise, self.lookup_field: instance_data.get(self.lookup_field)}
                    defaults = {k: v for k, v in instance_data.items() if k != self.lookup_field and k != 'enterprise'}
                    
                    obj, created = self.model.objects.update_or_create(**lookup_kwargs, defaults=defaults)
                    
                    if created: created_count += 1
                    else: updated_count += 1
        except IntegrityError as e:
            for key, name in self.unique_fields_for_error_handling.items():
                if key in str(e):
                    conflicting_value = current_item_for_error_reporting.get(name, '未知')
                    error_msg = f"数据冲突：{self.model._meta.verbose_name}的'{name}'字段值 '{conflicting_value}' 已存在。"
                    return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": f"数据库完整性错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"处理数据时发生未知错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        summary = f"同步完成。共处理 {len(data_list)} 条记录：{created_count} 条新增，{updated_count} 条更新。"
        return Response({"message": summary}, status=status.HTTP_200_OK)

class BaseAppendOnlySyncView(BaseSyncView):
    def post(self, request, *args, **kwargs):
        enterprise = request.auth.enterprise
        data_list = request.data
        if not isinstance(data_list, list):
            return Response({"error": "无效的数据格式，期望一个JSON数组"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fk_object_maps = self._prepare_fk_maps(enterprise, data_list)
            processed_data_list = self._process_and_validate_data(enterprise, data_list, fk_object_maps)
            
            objects_to_create = [self.model(**data) for data in processed_data_list]
            
            with transaction.atomic():
                self.model.objects.bulk_create(objects_to_create, ignore_conflicts=True)
        except Exception as e:
            return Response({"error": f"批量插入数据时出错: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": f"成功处理 {len(data_list)} 条记录的同步请求。"}, status=status.HTTP_200_OK)

class ProductBatchSyncView(BaseBatchSyncView):
    model = Product
    lookup_field = 'source_product_id'
    unique_fields_for_error_handling = {'enterprise_id_product_code': 'product_code'}

class StoreBatchSyncView(BaseBatchSyncView):
    model = Store
    lookup_field = 'source_store_id'
    unique_fields_for_error_handling = {'enterprise_id_name': 'name'}

class SupplierBatchSyncView(BaseBatchSyncView):
    model = Supplier
    lookup_field = 'source_supplier_id'
    unique_fields_for_error_handling = {'enterprise_id_supplier_code': 'supplier_code'}

class MemberBatchSyncView(BaseBatchSyncView):
    model = Member
    lookup_field = 'source_member_id'
    unique_fields_for_error_handling = {'enterprise_id_card_number': 'card_number'}
    foreign_key_lookups = {'issuing_store': ('store_id', Store, 'source_store_id')}

class EmployeeBatchSyncView(BaseBatchSyncView):
    model = Employee
    lookup_field = 'source_employee_id'
    unique_fields_for_error_handling = {'enterprise_id_employee_number': 'employee_number'}
    foreign_key_lookups = {'store': ('store_id', Store, 'source_store_id')}

class PurchaseBatchSyncView(BaseAppendOnlySyncView):
    model = Purchase
    foreign_key_lookups = {
        'product': ('product_id', Product, 'source_product_id'),
        'supplier': ('supplier_id', Supplier, 'source_supplier_id'),
    }

class SaleBatchSyncView(BaseAppendOnlySyncView):
    model = Sale
    foreign_key_lookups = {
        'product': ('product_id', Product, 'source_product_id'),
        'store': ('store_id', Store, 'source_store_id'),
        'member': ('member_id', Member, 'source_member_id'),
        'employee': ('employee_id', Employee, 'source_employee_id'),
    }

class InventorySnapshotBatchSyncView(BaseAppendOnlySyncView):
    model = InventorySnapshot
    foreign_key_lookups = {
        'product': ('product_id', Product, 'source_product_id'),
        'store': ('store_id', Store, 'source_store_id'),
    }
