# core/views/ui/store/index.py
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from django.db.models import Q
from core.models import Enterprise, Store

def _get_ent(request):
    ent_id = request.headers.get("X-Enterprise-ID") or request.query_params.get("enterprise")
    if ent_id:
        from django.core.exceptions import ObjectDoesNotExist
        try: return Enterprise.objects.get(id=ent_id)
        except ObjectDoesNotExist: return None
    profile = getattr(request.user, "userprofile", None)
    if profile and getattr(profile, "enterprise_id", None): return profile.enterprise
    return Enterprise.objects.filter(owner=request.user).first()

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "store_code", "name", "address", "business_scope"]

class StoreListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StoreSerializer
    def get_queryset(self):
        ent = _get_ent(self.request)
        qs = Store.objects.none() if not ent else Store.objects.filter(enterprise=ent).order_by("id")
        q = self.request.query_params.get("q")
        return qs.filter(Q(name__icontains=q) | Q(store_code__icontains=q)) if q else qs
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = int(request.query_params.get("page", 1))
        size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
        total = qs.count()
        data = self.get_serializer(qs[(page-1)*size: page*size], many=True).data
        return Response({"count": total, "results": data})

class StoreDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StoreSerializer
    def get_queryset(self):
        ent = _get_ent(self.request)
        return Store.objects.none() if not ent else Store.objects.filter(enterprise=ent)
