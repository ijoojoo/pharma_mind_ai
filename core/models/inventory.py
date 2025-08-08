from django.db import models
from .base import Enterprise
from .products import Product
from .transactions import Store

class InventorySnapshot(models.Model):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name="门店")
    snapshot_date = models.DateField(verbose_name="采集日期")
    quantity = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="数量")
    batch_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="批次号")
    batch_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="批号")
    production_date = models.DateField(blank=True, null=True, verbose_name="生产日期")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="有效期")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "库存快照"
        verbose_name_plural = verbose_name
        unique_together = (('enterprise', 'product', 'store', 'batch_number', 'snapshot_date'),)
