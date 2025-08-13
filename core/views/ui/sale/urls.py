# core/views/ui/sale/urls.py
from django.urls import path
from .index import SaleCreateView
urlpatterns = [
    path("create/", SaleCreateView.as_view(), name="sale-create"),
]
