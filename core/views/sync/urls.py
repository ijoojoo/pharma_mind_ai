# core/views/sync/urls.py
from django.urls import path
from ...views.sync import EmployeeBatchSyncView, InventorySnapshotBatchSyncView, MemberBatchSyncView, ProductBatchSyncView, PurchaseBatchSyncView, SaleBatchSyncView, StoreBatchSyncView, SupplierBatchSyncView

urlpatterns = [
    path("employee/", EmployeeBatchSyncView.as_view()),
    path("inventory_snapshot/", InventorySnapshotBatchSyncView.as_view()),
    path("member/", MemberBatchSyncView.as_view()),
    path("product/", ProductBatchSyncView.as_view()),
    path("purchase/", PurchaseBatchSyncView.as_view()),
    path("sale/", SaleBatchSyncView.as_view()),
    path("store/", StoreBatchSyncView.as_view()),
    path("supplier/", SupplierBatchSyncView.as_view()),
     
]
