# core/management/commands/generate_insights.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.db.models import F # 导入 F 表达式
from core.models import Product, SalesRecord, OperationalInsight

class Command(BaseCommand):
    help = '生成运营洞察并存入数据库'

    def handle(self, *args, **kwargs):
        self.stdout.write('开始生成运营洞察...')

        for user in User.objects.all():
            self.stdout.write(f'--- 正在为用户 [{user.username}] 分析数据 ---')
            user_stores = user.store_set.all()
            if not user_stores:
                continue

            # --- 1. 滞销品分析逻辑 (不变) ---
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recently_sold_product_ids = SalesRecord.objects.filter(
                store__in=user_stores,
                sold_at__gte=thirty_days_ago
            ).values_list('product_id', flat=True).distinct()
            slow_moving_products = Product.objects.filter(
                inventory_quantity__gt=0
            ).exclude(id__in=recently_sold_product_ids)

            for product in slow_moving_products:
                content = f"商品 '{product.name}' 已超过30天无销售，但仍有 {product.inventory_quantity} 件库存。建议进行促销或检查陈列。"
                obj, created = OperationalInsight.objects.update_or_create(
                    owner=user, insight_type='SLOW_MOVING', is_resolved=False,
                    defaults={'content': content}
                )
                if created: self.stdout.write(self.style.WARNING(f'  - 新增[滞销]洞察: {product.name}'))

            # --- 2. 新增：低库存分析逻辑 ---
            low_stock_products = Product.objects.filter(
                inventory_quantity__lte=F('low_stock_threshold') # 使用F表达式比较两个字段
            )

            for product in low_stock_products:
                content = f"商品 '{product.name}' 当前库存({product.inventory_quantity})已低于或等于阈值({product.low_stock_threshold})，请及时补货！"
                obj, created = OperationalInsight.objects.update_or_create(
                    owner=user, insight_type='LOW_STOCK', is_resolved=False,
                    defaults={'content': content}
                )
                if created: self.stdout.write(self.style.WARNING(f'  - 新增[低库存]洞察: {product.name}'))


        self.stdout.write(self.style.SUCCESS('...运营洞察生成完毕。'))