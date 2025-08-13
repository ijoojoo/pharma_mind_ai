from django.db import models
from .base import AuditableModel
from .enterprise import Enterprise

class Supplier(AuditableModel):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    source_supplier_id = models.CharField(max_length=100, verbose_name="源系统供应商ID")
    supplier_code = models.CharField(max_length=100, verbose_name="供应商编码")
    name = models.CharField(max_length=255, verbose_name="名称")

    class Meta:
        verbose_name = "供应商信息"
        verbose_name_plural = verbose_name
        unique_together = (('enterprise', 'source_supplier_id'), ('enterprise', 'supplier_code'))

    def __str__(self):
        return self.name