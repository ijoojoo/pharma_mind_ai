# file: scripts/dev/run_tests.sh
# purpose: 一键运行测试脚本（在项目根目录执行）
set -euo pipefail
python -m pip install -U pip
pip install -r requirements/dev.txt
pytest