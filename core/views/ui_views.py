import pandas as pd
from django.utils import timezone
from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from ..models import Enterprise, Product, Store, Sale, UserProfile
from ..serializers import ProductSerializer, StoreSerializer, SaleSerializer

def get_user_enterprise(user):
    try:
        if hasattr(user, 'profile') and user.profile.enterprise:
            return user.profile.enterprise
    except UserProfile.DoesNotExist:
        return None
    return None

class StoreListView(generics.ListAPIView):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        enterprise = get_user_enterprise(self.request.user)
        return Store.objects.filter(enterprise=enterprise) if enterprise else Store.objects.none()

class StoreDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        enterprise = get_user_enterprise(self.request.user)
        return Store.objects.filter(enterprise=enterprise) if enterprise else Store.objects.none()

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'product_code', 'source_product_id']
    def get_queryset(self):
        enterprise = get_user_enterprise(self.request.user)
        return Product.objects.filter(enterprise=enterprise) if enterprise else Product.objects.none()

class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        enterprise = get_user_enterprise(self.request.user)
        serializer.save(enterprise=enterprise)

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        enterprise = get_user_enterprise(self.request.user)
        return Product.objects.filter(enterprise=enterprise) if enterprise else Product.objects.none()

class ProductUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser,)
    def post(self, request, *args, **kwargs):
        enterprise = get_user_enterprise(request.user)
        if not enterprise: return Response({"error": "当前用户未关联任何企业"}, status=status.HTTP_400_BAD_REQUEST)
        if 'file' not in request.data: return Response({"error": "未提供文件"}, status=status.HTTP_400_BAD_REQUEST)
        
        file_obj = request.data['file']
        try:
            df = pd.read_excel(file_obj)
            required_columns = ['source_product_id', 'product_code', 'name', 'last_modified_at']
            if not all(col in df.columns for col in required_columns):
                return Response({"error": f"Excel文件缺少必要的列，请确保包含: {', '.join(required_columns)}"}, status=status.HTTP_400_BAD_REQUEST)

            products_to_create = [Product(enterprise=enterprise, **row_data) for row_data in df.to_dict('records')]
            Product.objects.bulk_create(products_to_create, ignore_conflicts=True)
            return Response({"message": f"成功导入 {len(products_to_create)} 条商品数据"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"处理文件时出错: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SaleCreateView(generics.CreateAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        enterprise = get_user_enterprise(self.request.user)
        serializer.save(enterprise=enterprise)

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        enterprise = get_user_enterprise(user)
        role = 'staff'
        try:
            if hasattr(user, 'profile'): role = user.profile.role
        except UserProfile.DoesNotExist: pass
        
        data = {
            "username": user.username,
            "nickname": enterprise.name if enterprise else user.username,
            "roles": [role],
            "permissions": ["*:*:*"],
            "avatar": "https://avatars.githubusercontent.com/u/44761321?v=4"
        }
        return Response({"success": True, "data": data})


class StoreKPIProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        enterprise = get_user_enterprise(request.user)
        stores = Store.objects.filter(enterprise=enterprise) if enterprise else []

        now = timezone.localtime()
        start = now.replace(hour=8, minute=0, second=0, microsecond=0)
        end = now.replace(hour=22, minute=0, second=0, microsecond=0)
        total_seconds = (end - start).total_seconds() or 1
        elapsed_seconds = (now - start).total_seconds()
        time_progress = max(0, min(elapsed_seconds / total_seconds, 1))

        data = []
        for idx, store in enumerate(stores, start=1):
            target = 1000
            completed = min(idx * 100, target)
            progress = completed / target
            data.append({
                "store_id": store.id,
                "store_name": store.name,
                "kpi_target": target,
                "kpi_completed": completed,
                "kpi_progress": round(progress, 2),
                "time_progress": round(time_progress, 2),
            })

        return Response({"success": True, "data": data})
