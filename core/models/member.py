from django.db import models
from .base import AuditableModel
from .enterprise import Enterprise
from .store import Store


class Member(AuditableModel):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    source_member_id = models.CharField(max_length=100, verbose_name="源系统会员ID")
    card_number = models.CharField(max_length=100, verbose_name="会员卡号")
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="姓名")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="手机号")
    address = models.CharField(max_length=500, blank=True, null=True, verbose_name="住址")
    issuing_store = models.ForeignKey(Store, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="办卡门店")
    current_points = models.IntegerField(default=0, verbose_name="当前积分")
    total_points = models.IntegerField(default=0, verbose_name="累计积分")
    total_consumption = models.DecimalField(max_digits=18, decimal_places=4, default=0, verbose_name="累计消费金额")
    tags = models.ManyToManyField('MemberTag', blank=True, verbose_name="标签")

    class Meta:
        verbose_name = "会员信息"
        verbose_name_plural = verbose_name
        unique_together = (('enterprise', 'source_member_id'),)

    def __str__(self):
        return self.name or self.card_number





