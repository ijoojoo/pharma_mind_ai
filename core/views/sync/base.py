from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ...authentication import EnterpriseAPIKeyAuthentication


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