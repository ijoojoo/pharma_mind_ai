from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from .base import BaseSyncView


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