# file: core/views/ai/system/docs.py
# purpose: 文档/Schema 视图（修复：Python format 与 JS 花括号冲突导致 KeyError）
# - 通过在 HTML 模板中对 JS 对象花括号进行转义（{{ 和 }})，避免 str.format 误解析
# - 提供 OpenAPI JSON 视图与错误码视图保持不变
from __future__ import annotations
import json
from django.views import View
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from core.openapi.ai_schema import build_schema, API_TITLE, API_VERSION
from core.ai.errors import list_error_codes


class AiOpenApiJsonView(View):
    """返回 OpenAPI JSON（供 Swagger UI 与前端客户端生成使用）。"""

    def get(self, request: HttpRequest):
        base = f"{request.scheme}://{request.get_host()}"
        doc = build_schema(server_url=base)
        return HttpResponse(
            json.dumps(doc, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
        )


class AiDocsView(View):
    """Swagger UI 文档页面（使用 CDN 资源；无第三方依赖）。
    注意：模板中 JS 对象的花括号必须使用成对转义 {{ }}，否则 Python 的 str.format 会误把它当成占位符。
    """

    HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{title} · API Docs</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  window.ui = SwaggerUIBundle({{
    url: "{schema_url}",
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis],
    layout: "BaseLayout",
    docExpansion: 'list',
    defaultModelExpandDepth: 2,
  }});
</script>
</body>
</html>
"""

    def get(self, request: HttpRequest):
        schema_url = reverse("ai_openapi_json")
        html = self.HTML.format(title=f"{API_TITLE} v{API_VERSION}", schema_url=schema_url)
        return HttpResponse(html, content_type="text/html; charset=utf-8")


class AiErrorCodesView(View):
    """输出统一错误码列表（JSON），便于前端渲染帮助/提示信息。"""

    def get(self, request: HttpRequest):
        data = list_error_codes()
        return HttpResponse(
            json.dumps({"success": True, "data": data}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
        )
