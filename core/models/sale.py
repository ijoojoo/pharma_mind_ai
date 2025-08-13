from django.db import models
from .enterprise import Enterprise
from .product import Product
from .store import Store


class Sale(models.Model):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    source_sale_id = models.CharField(max_length=100, verbose_name="源系统销售单据ID")
    source_sale_detail_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="源系统销售明细ID")
    store = models.ForeignKey(Store, on_delete=models.PROTECT, verbose_name="销售门店")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="销售商品")
    # --- 核心修改：使用字符串来定义外键关联 ---
    member = models.ForeignKey('core.Member', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="会员")
    employee = models.ForeignKey('core.Employee', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="销售员")
    # --- 修改结束 ---
    sale_time = models.DateTimeField(verbose_name="销售时间")
    quantity = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="数量")
    list_price = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="应收单价")
    actual_price = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="实收单价")
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="实收总金额")
    discount_amount = models.DecimalField(max_digits=18, decimal_places=4, default=0, verbose_name="折扣总金额")
    cost_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True, verbose_name="成本单价")
    total_cost_amount = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True, verbose_name="成本总金额")
    gross_profit_amount = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True, verbose_name="毛利额")
    batch_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="批次号")
    batch_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="批号")
    production_date = models.DateField(blank=True, null=True, verbose_name="生产日期")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="有效期")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "销售记录"
        verbose_name_plural = verbose_name
        unique_together = (('enterprise', 'source_sale_id', 'source_sale_detail_id'),)