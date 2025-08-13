# core/urls.py
from django.urls import path, include

urlpatterns = [
    # 前端 UI 接口
    #首页
    path("welcome/", include("core.views.ui.welcome.urls")),
    #用户
    path("user/", include("core.views.ui.user.urls")),
    #门店中心
    path("store/", include("core.views.ui.store.urls")),
    #商品中心
    path("product/", include("core.views.ui.product.urls")),
    #销售记录
    path("sale/", include("core.views.ui.sale.urls")),
    #库存中心
    # path("inventory/", include("core.views.ui.inventory.urls")),
    #系统设置
    # path("system/", include("core.views.ui.system.urls")),

    # 数据同步（数据连接器）
    path("sync/", include("core.views.sync.urls")),

    # AI
    path("ai/", include("core.views.ai.urls")),
]
