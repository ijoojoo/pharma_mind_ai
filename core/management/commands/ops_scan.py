# file: core/management/commands/ops_scan.py
# purpose: 定时扫描命令：可被 crontab/调度器调用；支持 --tenant 指定租户或遍历所有有规则的租户
from __future__ import annotations
from django.core.management.base import BaseCommand
from django.db.models import Value
from django.db.models.functions import Concat
from core.models.ai_ops import OpsAlertRule
from core.ai.ops.runner import run_ops_scan
from core.ai.ops.notify import notify_incidents


class Command(BaseCommand):
    help = "Run OPS anomaly scan for one or more tenants"

    def add_arguments(self, parser):
        """定义命令行参数：--tenant 指定单个租户；--silent 禁止通知。"""
        parser.add_argument("--tenant", type=str, default=None)
        parser.add_argument("--silent", action="store_true")

    def handle(self, *args, **opts):
        tenant = opts.get("tenant")
        silent = bool(opts.get("silent"))
        tenants: list[str]
        if tenant:
            tenants = [tenant]
        else:
            # 从规则表获取所有启用的租户列表
            tenants = list(OpsAlertRule.objects.filter(is_active=True).values_list("tenant_id", flat=True).distinct())
        total = 0
        for t in tenants:
            items = run_ops_scan(tenant_id=t, window={}, extra_rules=None)
            if not silent and items:
                notify_incidents(tenant_id=t, items=items)
            total += len(items)
        self.stdout.write(self.style.SUCCESS(f"ops_scan done: tenants={len(tenants)} new_items={total}"))