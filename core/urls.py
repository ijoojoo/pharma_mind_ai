from django.urls import path
from .views import (
    # UI Views
    StoreListView, StoreDetailView,
    ProductListView, ProductCreateView, ProductDetailView, ProductUploadView,
    SaleCreateView,
    UserInfoView, StoreKPIProgressView,
    # Sync Views
    ProductBatchSyncView,
    StoreBatchSyncView,
    SupplierBatchSyncView,
    PurchaseBatchSyncView,
    SaleBatchSyncView,
    InventorySnapshotBatchSyncView,
    MemberBatchSyncView,
    EmployeeBatchSyncView,
    # AI Views
    AIAutoCategorizeView
)

urlpatterns = [
    # --- 面向前端UI的API ---
    path('user/info/', UserInfoView.as_view(), name='user-info'),
    path('home/kpi-progress/', StoreKPIProgressView.as_view(), name='home-kpi-progress'),
    path('stores/', StoreListView.as_view(), name='store-list'),
    path('stores/<int:pk>/', StoreDetailView.as_view(), name='store-detail'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/create/', ProductCreateView.as_view(), name='product-create'),
    path('products/upload/', ProductUploadView.as_view(), name='product-upload'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('sales/create/', SaleCreateView.as_view(), name='sale-create'),

    # --- 数据连接器专用API端点 ---
    path('data/products/sync/', ProductBatchSyncView.as_view(), name='data-product-sync'),
    path('data/stores/sync/', StoreBatchSyncView.as_view(), name='data-store-sync'),
    path('data/suppliers/sync/', SupplierBatchSyncView.as_view(), name='data-supplier-sync'),
    path('data/purchases/sync/', PurchaseBatchSyncView.as_view(), name='data-purchase-sync'),
    path('data/sales/sync/', SaleBatchSyncView.as_view(), name='data-sale-sync'),
    path('data/inventory/sync/', InventorySnapshotBatchSyncView.as_view(), name='data-inventory-sync'),
    path('data/members/sync/', MemberBatchSyncView.as_view(), name='data-member-sync'),
    path('data/employees/sync/', EmployeeBatchSyncView.as_view(), name='data-employee-sync'),

    # --- AI功能API端点 ---
    path('ai/products/auto-categorize/', AIAutoCategorizeView.as_view(), name='ai-product-auto-categorize'),
]
