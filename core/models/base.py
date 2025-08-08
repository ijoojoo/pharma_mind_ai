from django.db import models
from django.contrib.auth.models import User

class AuditableModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True

class Enterprise(AuditableModel):
    name = models.CharField(max_length=255, verbose_name="企业名称")
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name="联系人")
    contact_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="联系电话")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="所属用户")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "企业信息"
        verbose_name_plural = verbose_name
