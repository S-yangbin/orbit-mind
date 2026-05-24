#!/usr/bin/env bash
# mars-cli 构建脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 构建 mars-cli ==="

# 清理旧产物
rm -rf dist/ build/ *.egg-info

# 安装构建依赖
pip install build --quiet

# 构建
python -m build

echo ""
echo "构建完成! 产物在 dist/ 目录:"
ls -la dist/
echo ""
echo "安装命令: pip install dist/mars_cli-*.whl"
