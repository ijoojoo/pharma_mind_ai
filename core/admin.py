from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# --- 核心修改：从新的模型文件中分别导入模型 ---
from .models.base import Enterprise
from .models.products import Product, Supplier
from .models.transactions import Store, Purchase, Sale
from .models.inventory import InventorySnapshot
from .models.profiles import Member, Tag, Employee, UserProfile
from .models.security import EnterpriseAPIKey

# --- 用户角色与企业管理 ---
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户配置'
    fields = ('enterprise', 'role') 

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# --- 企业与API密钥管理 ---
class EnterpriseAPIKeyInline(admin.StackedInline):
    model = EnterpriseAPIKey
    can_delete = True
    extra = 0
    fields = ('name', 'expiry_date', 'revoked')
    readonly_fields = ('prefix',)
    verbose_name_plural = 'API密钥'

    def get_fields(self, request, obj=None):
        if not obj:
            return ('name', 'key', 'expiry_date')
        return super().get_fields(request, obj)

@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'contact_person', 'contact_phone', 'created_at')
    search_fields = ('name', 'owner__username')
    inlines = [EnterpriseAPIKeyInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk and isinstance(instance, EnterpriseAPIKey):
                instance.enterprise = form.instance
                key = EnterpriseAPIKey.objects.assign_key(instance)
                messages.add_message(
                    request,
                    messages.WARNING,
                    (
                        "已成功生成新的API密钥，请立即复制并妥善保管，此密钥将不会再次完整显示: "
                        f"<code>{key}</code>"
                    ),
                    extra_tags="safe",
                )
        super().save_formset(request, form, formset, change)


# --- 其他业务模型管理 ---

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'enterprise', 'product_code', 'source_product_id', 'retail_price', 'manufacturer')
    search_fields = ('name', 'product_code', 'source_product_id')
    list_filter = ('enterprise', 'manufacturer')
    list_per_page = 20

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'enterprise', 'address')
    search_fields = ('name',)
    list_filter = ('enterprise',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'enterprise', 'supplier_code')
    search_fields = ('name', 'supplier_code')
    list_filter = ('enterprise',)

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('product', 'supplier', 'quantity', 'total_amount', 'purchase_date')
    list_filter = ('purchase_date', 'supplier__enterprise')
    date_hierarchy = 'purchase_date'

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'card_number', 'phone', 'enterprise', 'total_consumption')
    search_fields = ('name', 'card_number', 'phone')
    list_filter = ('enterprise',)
    filter_horizontal = ('tags',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'enterprise')
    list_filter = ('enterprise',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee_number', 'store', 'enterprise')
    search_fields = ('name', 'employee_number')
    list_filter = ('enterprise', 'store')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'store', 'quantity', 'total_amount', 'sale_time')
    list_filter = ('sale_time', 'store__enterprise', 'store')
    date_hierarchy = 'sale_time'

@admin.register(InventorySnapshot)
class InventorySnapshotAdmin(admin.ModelAdmin):
    list_display = ('product', 'store', 'quantity', 'snapshot_date')
    list_filter = ('snapshot_date', 'store__enterprise', 'store')
    date_hierarchy = 'snapshot_date'
