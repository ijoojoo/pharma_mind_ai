# file: core/management/commands/ai_purge_logs.py
# purpose: 清理过期 AI 日志（AiMessage / AiCallLog / AiRun）；保留期取自 settings.AI_LOG_RETENTION_DAYS，默认 90 天
from __future__ import annotations
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models.ai_logging import AiMessage, AiCallLog, AiRun


class Command(BaseCommand):
    help = "Purge expired AI logs"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=None, help="Override retention days")

    def handle(self, *args, **opts):
        days = opts.get("days") or getattr(__import__("django.conf").conf.settings, "AI_LOG_RETENTION_DAYS", 90)
        cutoff = timezone.now() - timedelta(days=int(days))
        m = AiMessage.objects.filter(created_at__lt=cutoff).delete()[0]
        c = AiCallLog.objects.filter(created_at__lt=cutoff).delete()[0]
        r = AiRun.objects.filter(created_at__lt=cutoff).delete()[0]
        self.stdout.write(self.style.SUCCESS(f"Purged messages={m}, calls={c}, runs={r}, before={cutoff.isoformat()}"))
