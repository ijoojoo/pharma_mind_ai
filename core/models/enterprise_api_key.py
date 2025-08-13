from django.db import models
from rest_framework_api_key.models import AbstractAPIKey
from .enterprise import Enterprise

class EnterpriseAPIKey(AbstractAPIKey):
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.CASCADE,
        related_name="api_keys",
        verbose_name="所属企业",
    )

    class Meta(AbstractAPIKey.Meta):
        verbose_name = "企业API密钥"
        verbose_name_plural = verbose_name
