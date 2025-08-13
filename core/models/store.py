from django.db import models
from .base import AuditableModel
from .enterprise import Enterprise

class Store(AuditableModel):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    source_store_id = models.CharField(max_length=100, verbose_name="源系统门店ID")
    store_code = models.CharField(max_length=100, verbose_name="门店编码")
    name = models.CharField(max_length=255, verbose_name="门店名称")
    address = models.CharField(max_length=500, blank=True, null=True, verbose_name="经营场所")
    business_scope = models.TextField(blank=True, null=True, verbose_name="经营范围")

    class Meta:
        verbose_name = "门店信息"
        verbose_name_plural = verbose_name
        unique_together = (('enterprise', 'source_store_id'),)

    def __str__(self):
        return self.name