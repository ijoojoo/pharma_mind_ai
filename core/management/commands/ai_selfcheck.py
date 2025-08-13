# file: core/management/commands/ai_selfcheck.py
# purpose: 管理命令：快速自检（可用于部署后 smoke-test / CI）。
from __future__ import annotations
from django.core.management.base import BaseCommand
from core.ai.diagnostics import run_health, run_selfcheck


class Command(BaseCommand):
    help = "Run AI health/selfcheck"

    def add_arguments(self, parser):
        parser.add_argument("--tenant", type=str, default=None, help="Optional tenant_id for selfcheck")

    def handle(self, *args, **opts):
        tenant = opts.get("tenant")
        if tenant:
            rep = run_selfcheck(tenant_id=tenant)
            self.stdout.write(self.style.SUCCESS(f"SELF-CHECK ok={rep.ok}"))
            for it in rep.items:
                self.stdout.write(f"- {it.name}: ok={it.ok} detail={it.detail}")
            if not rep.ok:
                raise SystemExit(2)
        else:
            rep = run_health()
            self.stdout.write(self.style.SUCCESS(f"HEALTH ok={rep.ok}"))
            for it in rep.items:
                self.stdout.write(f"- {it.name}: ok={it.ok} detail={it.detail}")
            if not rep.ok:
                raise SystemExit(2)
