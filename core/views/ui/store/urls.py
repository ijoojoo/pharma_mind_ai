# core/views/ui/store/urls.py
from django.urls import path
from .index import StoreListView, StoreDetailView
urlpatterns = [
    path("", StoreListView.as_view(), name="store-list"),
    path("<int:pk>/", StoreDetailView.as_view(), name="store-detail"),
]
