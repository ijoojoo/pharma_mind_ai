
from .product.index import (ProductListView, ProductDetailView, 
    ProductCreateView, ProductUploadView
)
from .sale.index import (
    SaleCreateView
)
from .store.index import (
    StoreListView, StoreDetailView
)
from .user.index import (
    UserInfoView
)


# 您可以有选择地定义 __all__ 来控制 `from .views import *` 导入的内容
__all__ = [
    "ProductListView", "ProductDetailView", 
    "ProductCreateView", "ProductUploadView",
    "SaleCreateView",
    "StoreListView", "StoreDetailView",
    "UserInfoView",
]
