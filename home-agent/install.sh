#!/usr/bin/env bash
# install.sh - 安装 Home Agent 为 systemd 服务
# 用法: sudo bash install.sh
set -euo pipefail

# ---- 配置 ----
APP_DIR="/home/syb/orbit-mind"
SERVICE_NAME="home-agent"
SERVICE_USER="syb"

echo "=== Home Agent 安装脚本 ==="

# 检查权限
if [ "$(id -u)" -ne 0 ]; then
    echo "错误: 请使用 sudo 运行此脚本"
    exit 1
fi

# 检查应用目录
if [ ! -d "$APP_DIR/home-agent" ]; then
    echo "错误: 应用目录 $APP_DIR/home-agent 不存在"
    exit 1
fi

# 安装 Python 依赖
echo "[1/4] 安装 Python 依赖..."
pip3 install --break-system-packages -r "$APP_DIR/home-agent/requirements.txt" 2>/dev/null || \
pip3 install -r "$APP_DIR/home-agent/requirements.txt"

# 创建日志目录
echo "[2/4] 创建日志目录..."
mkdir -p "$APP_DIR/logs"
chown "$SERVICE_USER:$SERVICE_USER" "$APP_DIR/logs"

# 生成 .env 文件（如果不存在）
ENV_FILE="$APP_DIR/home-agent/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[3/4] 从 config.yaml 生成 .env 文件..."
    # 从 config.yaml 提取 MNS 凭证写入 .env
    CONFIG_FILE="$APP_DIR/home-agent/config.yaml"
    if [ -f "$CONFIG_FILE" ]; then
        AK_ID=$(grep 'access_key_id' "$CONFIG_FILE" | head -1 | sed 's/.*: *"\?\([^"# ]*\)"\?.*/\1/' | tr -d ' ')
        AK_SECRET=$(grep 'access_key_secret' "$CONFIG_FILE" | head -1 | sed 's/.*: *"\?\([^"# ]*\)"\?.*/\1/' | tr -d ' ')
        ENDPOINT=$(grep 'endpoint' "$CONFIG_FILE" | head -1 | sed 's/.*: *"\?\([^"# ]*\)"\?.*/\1/' | tr -d ' ')
        QUEUE=$(grep 'queue_name' "$CONFIG_FILE" | head -1 | sed 's/.*: *"\?\([^"# ]*\)"\?.*/\1/' | tr -d ' ')

        cat > "$ENV_FILE" << EOF
MNS_ENDPOINT=$ENDPOINT
ALIBABA_CLOUD_ACCESS_KEY_ID=$AK_ID
ALIBABA_CLOUD_ACCESS_KEY_SECRET=$AK_SECRET
MNS_QUEUE_NAME=$QUEUE
EOF
        chown "$SERVICE_USER:$SERVICE_USER" "$ENV_FILE"
        chmod 600 "$ENV_FILE"
        echo "    .env 文件已生成"
    else
        echo "    警告: config.yaml 不存在，请手动创建 $ENV_FILE"
    fi
else
    echo "[3/4] .env 文件已存在，跳过"
fi

# 安装 systemd service
echo "[4/4] 安装 systemd service..."
cp "$APP_DIR/home-agent/home-agent.service" "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo ""
echo "=== 安装完成 ==="
echo ""
echo "启动服务:   sudo systemctl start $SERVICE_NAME"
echo "查看状态:   sudo systemctl status $SERVICE_NAME"
echo "查看日志:   sudo journalctl -u $SERVICE_NAME -f"
echo "审计日志:   ls $APP_DIR/logs/"
echo ""
