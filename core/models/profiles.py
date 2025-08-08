from django.db import models
from django.contrib.auth.models import User
from .base import AuditableModel, Enterprise
# --- ↓↓↓ 核心修改：移除了对 transactions 的直接导入，以避免循环依赖 ↓↓↓ ---
# from .transactions import Store 
# --- ↑↑↑ 修改结束 ↑↑↑ ---

class Member(AuditableModel):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    source_member_id = models.CharField(max_length=100, verbose_name="源系统会员ID")
    card_number = models.CharField(max_length=100, verbose_name="会员卡号")
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="姓名")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="手机号")
    address = models.CharField(max_length=500, blank=True, null=True, verbose_name="住址")
    # --- ↓↓↓ 核心修改：使用字符串 'core.Store' 来定义外键关联 ↓↓↓ ---
    issuing_store = models.ForeignKey('core.Store', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="办卡门店")
    # --- ↑↑↑ 修改结束 ↑↑↑ ---
    current_points = models.IntegerField(default=0, verbose_name="当前积分")
    total_points = models.IntegerField(default=0, verbose_name="累计积分")
    total_consumption = models.DecimalField(max_digits=18, decimal_places=4, default=0, verbose_name="累计消费金额")
    tags = models.ManyToManyField('Tag', blank=True, verbose_name="标签")

    class Meta:
        verbose_name = "会员信息"
        verbose_name_plural = verbose_name
        unique_together = (('enterprise', 'source_member_id'),)

    def __str__(self):
        return self.name or self.card_number

class Tag(models.Model):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    name = models.CharField(max_length=100, verbose_name="标签名称")

    class Meta:
        verbose_name = "会员标签"
        verbose_name_plural = verbose_name
        unique_together = ('enterprise', 'name')

    def __str__(self):
        return self.name

class Employee(AuditableModel):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, verbose_name="所属企业")
    source_employee_id = models.CharField(max_length=100, verbose_name="源系统职员ID")
    # --- ↓↓↓ 核心修改：使用字符串 'core.Store' 来定义外键关联 ↓↓↓ ---
    store = models.ForeignKey('core.Store', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="所属门店")
    # --- ↑↑↑ 修改结束 ↑↑↑ ---
    employee_number = models.CharField(max_length=100, verbose_name="工号")
    name = models.CharField(max_length=100, verbose_name="姓名")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="手机号")

    class Meta:
        verbose_name = "职员信息"
        verbose_name_plural = verbose_name
        unique_together = (('enterprise', 'source_employee_id'), ('enterprise', 'employee_number'))

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLE_CHOICES = (('owner', '企业主'), ('manager', '店长'), ('staff', '店员'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="用户")
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, null=True, blank=True, verbose_name="所属企业")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff', verbose_name='角色')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = "用户配置"
        verbose_name_plural = verbose_name
