#!/bin/bash
# mars-cli 部署脚本
# 用于部署到 Hermes Agent 服务器并更新 SKILL.md

set -e

echo "========================================="
echo "mars-cli 部署脚本"
echo "========================================="

# 加载项目根目录 .env（含服务器 IP，已加入 .gitignore）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../../.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "错误: 未找到 ${ENV_FILE}，请创建并添加 HERMES_SERVER_IP=x.x.x.x"
    exit 1
fi

# 配置变量（从 .env 读取，避免硬编码暴露 IP）
HERMES_IP="${HERMES_SERVER_IP:?请在 .env 中设置 HERMES_SERVER_IP}"
HERMES_SERVER="root@${HERMES_IP}"
SKILL_DIR="/root/.hermes/skills/smart-home/mars-cli"
VENV_DIR="/usr/local/lib/hermes-agent/venv"

# 项目内路径
SKILL_SRC="${SCRIPT_DIR}/../../home-agent-skill/mars-cli/SKILL.md"

echo ""
echo "步骤 1: 清理旧构建产物..."
cd "$SCRIPT_DIR"
rm -rf dist/ build/ *.egg-info
echo "✓ 清理完成"

echo ""
echo "步骤 2: 构建 mars-cli wheel..."
uv run python -m build 2>&1 | tail -5
WHEEL_FILE=$(ls dist/mars_cli-*.whl 2>/dev/null | head -1)
if [ -z "$WHEEL_FILE" ]; then
    echo "错误: 未找到 wheel 文件，构建失败"
    exit 1
fi
echo "✓ 构建完成: $(basename "$WHEEL_FILE")"

echo ""
echo "步骤 3: 上传 wheel 到服务器..."
scp "$WHEEL_FILE" $HERMES_SERVER:/tmp/
echo "✓ 上传完成"

echo ""
echo "步骤 4: 在服务器上安装 mars-cli..."
ssh $HERMES_SERVER << ENDSSH
${VENV_DIR}/bin/pip install --force-reinstall /tmp/$(basename "$WHEEL_FILE") 2>&1 | tail -5
rm -f /tmp/$(basename "$WHEEL_FILE")
echo "✓ 安装完成"
ENDSSH

echo ""
echo "步骤 5: 上传 SKILL.md..."
if [ -f "$SKILL_SRC" ]; then
    ssh $HERMES_SERVER "mkdir -p ${SKILL_DIR}"
    scp "$SKILL_SRC" "${HERMES_SERVER}:${SKILL_DIR}/SKILL.md"
    echo "✓ SKILL.md 上传完成"
else
    echo "警告: 未找到 $SKILL_SRC，跳过 SKILL.md 上传"
fi

echo ""
echo "步骤 6: 验证部署..."
ssh $HERMES_SERVER << 'ENDSSH'
echo "--- mars-cli 版本信息 ---"
/usr/local/bin/mars-cli --help 2>&1 | head -5
echo ""
echo "--- stars 模块 ---"
/usr/local/bin/mars-cli stars --help 2>&1 | grep -E "summary|list|add|redeem|delete"
echo ""
echo "--- dashboard screensaver ---"
/usr/local/bin/mars-cli dashboard --help 2>&1 | grep screensaver
echo "✓ 验证完成"
ENDSSH

# 清理本地构建产物
rm -rf dist/ build/ *.egg-info
echo "✓ 本地构建产物已清理"

echo ""
echo "========================================="
echo "mars-cli 部署完成!"
echo "========================================="
echo ""
echo "服务器: ${HERMES_SERVER}"
echo "SKILL路径: ${SKILL_DIR}/SKILL.md"
echo ""
