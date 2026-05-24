#!/bin/bash
# mars-sandbox 部署脚本
# 用于部署到服务器并启动服务

set -e

echo "========================================="
echo "Mars Sandbox 部署脚本 (WebSocket版本)"
echo "========================================="

# 配置变量
SERVER="root@8.213.135.161"
REMOTE_DIR="/opt/mars-sandbox"
SERVICE_NAME="mars-sandbox"

echo ""
echo "步骤 1: 打包后端代码..."
cd backend
tar -czf ../mars-sandbox-backend.tar.gz \
    app/ \
    requirements.txt \
    .env.example
cd ..
echo "✓ 打包完成"

echo ""
echo "步骤 2: 上传到服务器..."
scp mars-sandbox-backend.tar.gz $SERVER:$REMOTE_DIR/
echo "✓ 上传完成"

echo ""
echo "步骤 3: 在服务器上部署..."
ssh $SERVER << 'ENDSSH'
cd /opt/mars-sandbox

# 停止旧服务
systemctl stop mars-sandbox 2>/dev/null || true

# 解压新代码
tar -xzf mars-sandbox-backend.tar.gz

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 确保.env文件存在
if [ ! -f .env ]; then
    echo "警告: .env文件不存在,请手动配置"
    cp .env.example .env
fi

# 设置权限
chown -R www-data:www-data /opt/mars-sandbox 2>/dev/null || true

echo "✓ 部署完成"
ENDSSH

echo ""
echo "步骤 4: 启动服务..."
ssh $SERVER << 'ENDSSH'
cd /opt/mars-sandbox
source venv/bin/activate

# 启动服务
systemctl start mars-sandbox
systemctl status mars-sandbox --no-pager

echo "✓ 服务已启动"
ENDSSH

# 清理
rm -f mars-sandbox-backend.tar.gz

echo ""
echo "========================================="
echo "部署完成!"
echo "========================================="
echo ""
echo "WebSocket端点: ws://8.213.135.161:8888/ws/agent/{node_id}"
echo "HTTP API: http://8.213.135.161:8888/api/commands"
echo "API文档: http://8.213.135.161:8888/docs"
echo ""
echo "查看日志: ssh $SERVER 'journalctl -u mars-sandbox -f'"
echo ""
