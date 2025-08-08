# 该文件使 Python 将 'views' 目录视为一个包。
# 它也作为一个中心点来导入所有的视图，以便 Django 能够找到它们。

from .ui_views import (
    StoreListView, StoreDetailView, ProductListView, ProductCreateView, 
    ProductDetailView, ProductUploadView, SaleCreateView, UserInfoView
)
from .sync_views import (
    ProductBatchSyncView, StoreBatchSyncView, SupplierBatchSyncView,
    PurchaseBatchSyncView, SaleBatchSyncView, InventorySnapshotBatchSyncView,
    MemberBatchSyncView, EmployeeBatchSyncView
)
from .ai_views import AIAutoCategorizeView

# 您可以有选择地定义 __all__ 来控制 `from .views import *` 导入的内容
__all__ = [
    'StoreListView', 'StoreDetailView', 'ProductListView', 'ProductCreateView',
    'ProductDetailView', 'ProductUploadView', 'SaleCreateView', 'UserInfoView',
    'ProductBatchSyncView', 'StoreBatchSyncView', 'SupplierBatchSyncView',
    'PurchaseBatchSyncView', 'SaleBatchSyncView', 'InventorySnapshotBatchSyncView',
    'MemberBatchSyncView', 'EmployeeBatchSyncView',
    'AIAutoCategorizeView',
]
