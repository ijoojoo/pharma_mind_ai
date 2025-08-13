from django.db import models
from .base import AuditableModel
from .enterprise import Enterprise
from .store import Store

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
