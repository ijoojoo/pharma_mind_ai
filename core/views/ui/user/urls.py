
# core/views/ui/user/urls.py
from django.urls import path
from .index import UserInfoView
urlpatterns = [
    path("info/", UserInfoView.as_view(), name="user-info"),
]
