from django.db import models
from django.contrib.auth.models import User
from .base import AuditableModel
from .enterprise import Enterprise

class UserProfile(AuditableModel):
    ROLE_CHOICES = (('owner', '企业主'), ('manager', '店长'), ('staff', '店员'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="用户")
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, null=True, blank=True, verbose_name="所属企业")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff', verbose_name='角色')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = "用户配置"
        verbose_name_plural = verbose_name