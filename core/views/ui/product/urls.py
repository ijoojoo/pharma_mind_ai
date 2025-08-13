# core/views/ui/product/urls.py
from django.urls import path
from .index import (
    ProductListView, ProductDetailView,
    ProductCreateView, ProductUploadView
)
urlpatterns = [
    path("", ProductListView.as_view(), name="product-list"),
    path("<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("create/", ProductCreateView.as_view(), name="product-create"),
    path("upload/", ProductUploadView.as_view(), name="product-upload"),
]
