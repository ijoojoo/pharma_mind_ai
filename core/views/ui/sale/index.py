# core/views/ui/sale/index.py
from rest_framework import permissions, serializers, generics
from django.utils import timezone
from core.models import Sale, Store, Product, Enterprise


def _get_ent(request):
    ent_id = request.headers.get("X-Enterprise-ID") or request.query_params.get("enterprise")
    if ent_id:
        from django.core.exceptions import ObjectDoesNotExist
        try: return Enterprise.objects.get(id=ent_id)
        except ObjectDoesNotExist: return None
    profile = getattr(request.user, "userprofile", None)
    if profile and getattr(profile, "enterprise_id", None): return profile.enterprise
    return Enterprise.objects.filter(owner=request.user).first()

class SaleCreateSerializer(serializers.ModelSerializer):
    store_id = serializers.IntegerField(write_only=True)
    product_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = Sale
        fields = ["store_id","product_id","sale_time","quantity","list_price","actual_price"]
    def create(self, validated_data):
        ent = _get_ent(self.context["request"])
        store = Store.objects.get(id=validated_data.pop("store_id"), enterprise=ent)
        product = Product.objects.get(id=validated_data.pop("product_id"), enterprise=ent)
        return Sale.objects.create(
            enterprise=ent,
            source_sale_id=f"UI-{timezone.now().timestamp()}",
            store=store, product=product,
            sale_time=validated_data.get("sale_time") or timezone.now(),
            quantity=validated_data["quantity"],
            list_price=validated_data["list_price"],
            actual_price=validated_data["actual_price"],
            total_amount=validated_data["actual_price"] * validated_data["quantity"],
        )

class SaleCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SaleCreateSerializer
    def get_queryset(self): return Sale.objects.none()
