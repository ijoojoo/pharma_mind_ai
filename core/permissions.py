from rest_framework_api_key.permissions import BaseHasAPIKey
from .models import EnterpriseAPIKey

class HasEnterpriseAPIKey(BaseHasAPIKey):
    """
    一个专属的权限类，
    它明确告诉认证系统：请使用我们的 EnterpriseAPIKey 模型来验证传入的密钥。
    """
    model = EnterpriseAPIKey
