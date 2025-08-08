from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import EnterpriseAPIKey

class EnterpriseAPIKeyAuthentication(BaseAuthentication):
    """
    一个专属的认证类，用于验证来自数据连接器的API密钥。
    """
    def authenticate(self, request):
        # 1. 从请求头中获取API密钥 (Django会自动将 Api-Key 转换为 HTTP_API_KEY)
        key = request.META.get('HTTP_API_KEY')
        if not key:
            return None # 如果没有提供密钥，则放弃认证

        # 2. 使用库提供的方法来安全地验证密钥
        try:
            api_key = EnterpriseAPIKey.objects.get_from_key(key)
        except EnterpriseAPIKey.DoesNotExist:
            raise AuthenticationFailed('无效的 API 密钥。')

        # --- ↓↓↓ 核心修改：修复 'is_expired' 错误 ↓↓↓ ---
        # 3. 检查密钥是否已过期或被撤销
        if api_key.expiry_date and api_key.expiry_date < timezone.now():
            raise AuthenticationFailed('API 密钥已过期。')
        # --- ↑↑↑ 修改结束 ↑↑↑ ---
        
        if api_key.revoked:
            raise AuthenticationFailed('API 密钥已被撤销。')

        # 4. 认证成功，返回用户和密钥对象
        #    这将使得 request.user 和 request.auth 在视图中可用
        user = api_key.enterprise.owner
        return (user, api_key)

    def authenticate_header(self, request):
        # 用于在401响应中提示客户端
        return 'Api-Key'
