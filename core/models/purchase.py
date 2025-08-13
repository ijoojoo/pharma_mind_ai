from django.db import models
from .enterprise import Enterprise
from .product import Product
from .supplier import Supplier


class Purchase(models.Model):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    source_purchase_id = models.CharField(max_length=100, verbose_name="源系统采购单据ID")
    document_number = models.CharField(max_length=100, verbose_name="单据编号")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="商品")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, verbose_name="供应商")
    purchase_date = models.DateField(verbose_name="采购日期")
    quantity = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="数量")
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="单价")
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="总金额")
    batch_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="批次号")
    batch_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="批号")
    production_date = models.DateField(blank=True, null=True, verbose_name="生产日期")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="有效期")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "采购记录"
        verbose_name_plural = verbose_name
        unique_together = (('enterprise', 'source_purchase_id', 'product'),)