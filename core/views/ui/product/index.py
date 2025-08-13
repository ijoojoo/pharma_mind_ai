# core/views/ui/product/index.py
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models.product import Product
from core.models import Enterprise

def _get_ent(request):
    ent_id = request.headers.get("X-Enterprise-ID") or request.query_params.get("enterprise")
    if ent_id:
        from django.core.exceptions import ObjectDoesNotExist
        try: return Enterprise.objects.get(id=ent_id)
        except ObjectDoesNotExist: return None
    profile = getattr(request.user, "userprofile", None)
    if profile and getattr(profile, "enterprise_id", None): return profile.enterprise
    return Enterprise.objects.filter(owner=request.user).first()

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "barcode", "spec", "unit", "category_l1", "category_l2", "category_l3"]

class ProductListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductSerializer
    def get_queryset(self):
        ent = _get_ent(self.request)
        qs = Product.objects.none() if not ent else Product.objects.filter(enterprise=ent).order_by("id")
        q = self.request.query_params.get("q")
        return qs.filter(name__icontains=q) if q else qs

class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductSerializer
    def get_queryset(self):
        ent = _get_ent(self.request)
        return Product.objects.none() if not ent else Product.objects.filter(enterprise=ent)

class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "barcode", "spec", "unit", "category_l1", "category_l2", "category_l3"]
    def create(self, validated_data):
        ent = _get_ent(self.context["request"])
        validated_data["enterprise"] = ent
        return super().create(validated_data)

class ProductCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductCreateSerializer
    def get_queryset(self): return Product.objects.none()

class ProductUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        # file = request.FILES.get("file")
        return Response({"detail": "已接收，解析导入待实现"}, status=status.HTTP_202_ACCEPTED)
