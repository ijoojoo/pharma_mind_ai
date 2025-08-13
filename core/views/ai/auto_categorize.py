from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import json

from ...authentication import EnterpriseAPIKeyAuthentication
from ...models import Product


# 这是一个模拟的AI API调用函数，在实际应用中，您会在这里调用真实的Gemini API
def call_gemini_api_for_categorization(products_info):
    # 1. 构建Prompt
    prompt = f"""
    你是一个专业的医药行业数据分析师。请根据以下商品列表（格式为：ID | 商品名称 | 规格 | 生产企业），为每一个商品生成一个包含三个级别分类的JSON对象。
    请严格遵循以下JSON格式，不要添加任何额外的解释或说明：
    [
        {{ "id": 商品ID, "category_l1": "一级分类", "category_l2": "二级分类", "category_l3": "三级分类" }},
        ...
    ]

    商品列表如下：
    {products_info}
    """
    print("--- Sending Prompt to AI ---")
    print(prompt)
    
    # 2. 模拟AI返回的JSON字符串
    mock_response_json = json.dumps([
        { "id": 1, "category_l1": "化学药", "category_l2": "抗感染药", "category_l3": "青霉素类" },
        { "id": 2, "category_l1": "化学药", "category_l2": "解热镇痛", "category_l3": "非甾体抗炎药" },
        { "id": 4, "category_l1": "保健食品", "category_l2": "维生素与矿物质", "category_l3": "维生素C" }
    ])
    
    return mock_response_json


class AIAutoCategorizeView(APIView):
    authentication_classes = [EnterpriseAPIKeyAuthentication] # 或者使用JWT认证，取决于调用场景
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        enterprise = request.auth.enterprise if hasattr(request.auth, 'enterprise') else get_user_enterprise(request.user)
        if not enterprise:
            return Response({"error": "无法确定企业信息"}, status=403)

        # 1. 查找所有尚未分类的商品 (这里我们只取前10个作为示例)
        products_to_categorize = Product.objects.filter(
            enterprise=enterprise, 
            category_standard_l1__isnull=True
        )[:10]

        if not products_to_categorize:
            return Response({"message": "所有商品均已分类，无需操作。"})

        # 2. 准备用于AI分析的文本信息
        products_info = "\n".join([
            f"{p.id} | {p.name} | {p.specification} | {p.manufacturer}" 
            for p in products_to_categorize
        ])

        # 3. 调用AI进行分析
        try:
            ai_response_str = call_gemini_api_for_categorization(products_info)
            categorization_results = json.loads(ai_response_str)
        except Exception as e:
            return Response({"error": f"AI分析失败或返回格式错误: {str(e)}"}, status=500)

        # 4. 使用事务，将AI返回的结果更新到数据库
        updated_count = 0
        try:
            with transaction.atomic():
                for result in categorization_results:
                    product_id = result.get("id")
                    Product.objects.filter(id=product_id, enterprise=enterprise).update(
                        category_standard_l1=result.get("category_l1"),
                        category_standard_l2=result.get("category_l2"),
                        category_standard_l3=result.get("category_l3")
                    )
                    updated_count += 1
        except Exception as e:
            return Response({"error": f"更新数据库时出错: {str(e)}"}, status=500)

        return Response({"message": f"AI自动分类完成！成功更新 {updated_count} 条商品信息。"})