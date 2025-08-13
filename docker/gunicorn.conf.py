# file: docker/gunicorn.conf.py
# purpose: Gunicorn 配置（从环境读取核心参数）；默认 gthread worker，兼容 WSGI；如需 ASGI 请设置 worker_class
import multiprocessing
import os

bind = os.getenv("BIND", "0.0.0.0:8000")
workers = int(os.getenv("GUNICORN_WORKERS", str(multiprocessing.cpu_count() * 2 + 1)))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")  # ASGI: "uvicorn.workers.UvicornWorker"
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# 优雅停止
graceful_timeout = 30
keepalive = 5

# 安全 headers
forwarded_allow_ips = "*"
proxy_allow_ips = "*"