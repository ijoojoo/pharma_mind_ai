# file: docker/Dockerfile
# purpose: 生产镜像（多阶段构建，最小化体积）；默认以 Gunicorn + Django WSGI 启动
# 使用：
#   docker build -t pharma-mind-ai:latest -f docker/Dockerfile .
#   docker run --env-file deploy/env.example -p 8000:8000 pharma-mind-ai:latest
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# 系统依赖（psycopg2/uvicorn/gunicorn/slugify 可能需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先拷贝依赖声明，便于缓存
COPY requirements/production.txt /app/requirements/production.txt
RUN pip install -r requirements/production.txt

# 拷贝项目代码
COPY . /app

# 创建非 root 用户
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 入口：可切换 WSGI/ASGI
ENV GUNICORN_APP=config.wsgi:application \
    GUNICORN_WORKERS=3 \
    GUNICORN_THREADS=4 \
    GUNICORN_TIMEOUT=120

# 收集静态资源（若未配置可忽略错误）
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000
ENTRYPOINT ["bash", "docker/entrypoint.sh"]