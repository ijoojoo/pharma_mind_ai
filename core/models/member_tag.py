from django.db import models
from .base import AuditableModel
from .enterprise import Enterprise


class MemberTag(AuditableModel):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    name = models.CharField(max_length=100, verbose_name="标签名称")

    class Meta:
        verbose_name = "会员标签"
        verbose_name_plural = verbose_name
        unique_together = ('enterprise', 'name')

    def __str__(self):
        return self.name