# core/views/ui/user/index.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from core.models import Enterprise

class UserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, "userprofile", None)
        enterprise = None
        if profile and getattr(profile, "enterprise_id", None):
            enterprise = profile.enterprise
        else:
            enterprise = Enterprise.objects.filter(owner=user).first()
        return Response({
            "username": user.username,
            "is_staff": user.is_staff,
            "enterprise": {"id": getattr(enterprise, "id", None), "name": getattr(enterprise, "name", None)}
        })
