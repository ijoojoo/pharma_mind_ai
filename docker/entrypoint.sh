 file: docker/entrypoint.sh
# purpose: 容器入口脚本：迁移 → 启动 Gunicorn；
# 可通过 GUNICORN_APP=config.asgi:application + UvicornWorker 切换到 ASGI
set -euo pipefail

# 数据库迁移（失败不退出，避免首次无 DB 时阻塞）
python manage.py migrate || true

# 可选：加载最小演示数据
if [ "${LOAD_AI_FIXTURES:-0}" = "1" ]; then
  python manage.py loaddata core/fixtures/ai_min.json || true
fi

# 启动 Gunicorn
exec gunicorn "$GUNICORN_APP" \
  --config docker/gunicorn.conf.py