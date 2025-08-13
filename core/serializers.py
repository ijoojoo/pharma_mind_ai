from rest_framework import serializers
#导入模型 ---
from .models.employee import Employee
from .models.enterprise_api_key import EnterpriseAPIKey
from .models.enterprise import Enterprise
from .models.inventory_snapshot import InventorySnapshot
from .models.member_tag import MemberTag
from .models.member import Member
from .models.product import Product
from .models.purchase import Purchase
from .models.sale import Sale
from .models.store import Store
from .models.supplier import Supplier
from .models.user_profile import UserProfile

class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = '__all__'

class EnterpriseAPIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseAPIKey
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'

class MemberTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberTag
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = '__all__'

class InventorySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorySnapshot
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
