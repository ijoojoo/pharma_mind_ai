from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.response import Response

from .base import BaseSyncView


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