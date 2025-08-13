# file: scripts/setup/install_deps.sh
# purpose: 一键安装依赖（当前虚拟环境）
set -euo pipefail
python -m pip install -U pip wheel setuptools
pip install -r requirements.txt