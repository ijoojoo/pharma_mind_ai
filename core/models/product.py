from django.db import models
from .base import AuditableModel
from .enterprise import Enterprise

class Product(AuditableModel):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    source_product_id = models.CharField(max_length=100, verbose_name="源系统商品ID")
    product_code = models.CharField(max_length=100, verbose_name="商品编码")
    name = models.CharField(max_length=255, verbose_name="商品名称")
    specification = models.CharField(max_length=255, blank=True, null=True, verbose_name="规格")
    unit = models.CharField(max_length=50, blank=True, null=True, verbose_name="单位")
    manufacturer = models.CharField(max_length=255, blank=True, null=True, verbose_name="生产企业")
    marketing_authorization_holder = models.CharField(max_length=255, blank=True, null=True, verbose_name="上市许可持有人")
    approval_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="批准文号")
    dosage_form = models.CharField(max_length=100, blank=True, null=True, verbose_name="剂型")
    responsible_person = models.CharField(max_length=100, blank=True, null=True, verbose_name="负责人")
    retail_price = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="零售价")
    member_price = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="会员价")
    category_l1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="大分类")
    category_l2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="中分类")
    category_l3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="小分类")
    category_l4 = models.CharField(max_length=100, blank=True, null=True, verbose_name="细分类")
    category_enterprise_l1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="企业-大分类")
    category_enterprise_l2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="企业-中分类")
    category_enterprise_l3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="企业-小分类")
    category_enterprise_l4 = models.CharField(max_length=100, blank=True, null=True, verbose_name="企业-细分类")
    standard_product_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="商品本位码")
    medicare_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="医保编码")
    last_modified_at = models.DateTimeField(verbose_name="最后修改时间")

    class Meta:
        verbose_name = "商品信息"
        verbose_name_plural = verbose_name
        unique_together = (('enterprise', 'source_product_id'), ('enterprise', 'product_code'))

    def __str__(self):
        return self.name


