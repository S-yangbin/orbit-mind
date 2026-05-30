#!/bin/bash
# mars-sandbox 部署脚本
# 用于部署到服务器并启动服务

set -e

echo "========================================="
echo "Mars Sandbox 部署脚本 (WebSocket版本)"
echo "========================================="

# 配置变量
SERVER="root@<your-server-ip>"
REMOTE_DIR="/opt/mars-sandbox"
SERVICE_NAME="mars-sandbox"

echo ""
echo "步骤 1: 构建前端..."
cd frontend

# 检查 pnpm 是否可用
if command -v pnpm &> /dev/null; then
    echo "使用 pnpm 安装依赖..."
    pnpm install
    echo "使用 pnpm 构建前端..."
    pnpm run build
elif command -v npm &> /dev/null; then
    echo "使用 npm 安装依赖..."
    npm install
    echo "使用 npm 构建前端..."
    npm run build
else
    echo "错误: 未找到 pnpm 或 npm"
    exit 1
fi

cd ..
echo "✓ 前端构建完成"

echo ""
echo "步骤 2: 打包后端和前端代码..."
cd backend
tar -czf ../mars-sandbox-backend.tar.gz \
    app/ \
    requirements.txt
cd ..

# 打包前端编译产物
cd frontend
tar -czf ../mars-sandbox-frontend.tar.gz \
    dist/
cd ..
echo "✓ 打包完成"

echo ""
echo "步骤 3: 上传到服务器..."
scp mars-sandbox-backend.tar.gz $SERVER:$REMOTE_DIR/
scp mars-sandbox-frontend.tar.gz $SERVER:$REMOTE_DIR/
scp mars-sandbox.service $SERVER:$REMOTE_DIR/
echo "✓ 上传完成"

echo ""
echo "步骤 4: 在服务器上部署..."
ssh $SERVER << 'ENDSSH'
cd /opt/mars-sandbox

# 停止旧服务
systemctl stop mars-sandbox 2>/dev/null || true

# 解压后端代码
tar -xzf mars-sandbox-backend.tar.gz

# 激活虚拟环境
source venv/bin/activate

# 安装后端依赖
pip install -r requirements.txt

# 确保.env文件存在
if [ ! -f .env ]; then
    echo "警告: .env文件不存在,请手动配置"
    cp .env.example .env 2>/dev/null || echo "请手动创建.env文件"
fi

echo "✓ 后端部署完成"

# 部署前端编译产物
echo ""
echo "步骤 4.1: 部署前端..."
mkdir -p frontend
tar -xzf mars-sandbox-frontend.tar.gz -C frontend/

echo "✓ 前端部署完成"

# 安装 systemd service 文件
cp /opt/mars-sandbox/mars-sandbox.service /etc/systemd/system/mars-sandbox.service
systemctl daemon-reload
echo "✓ Service 文件已更新"

# 设置权限
chown -R www-data:www-data /opt/mars-sandbox 2>/dev/null || true

# 清理部署产物和macOS资源文件
rm -f mars-sandbox-backend.tar.gz mars-sandbox-frontend.tar.gz mars-sandbox.service
find /opt/mars-sandbox -maxdepth 2 -name '._*' -delete 2>/dev/null || true

echo "✓ 部署完成"
ENDSSH

echo ""
echo "步骤 5: 启动服务..."
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
rm -f mars-sandbox-frontend.tar.gz

echo ""
echo "========================================="
echo "部署完成!"
echo "========================================="
echo ""
echo "前端页面: http://<your-server-ip>:8888/"
echo "WebSocket端点: ws://<your-server-ip>:8888/ws/agent/{node_id}"
echo "HTTP API: http://<your-server-ip>:8888/api/commands"
echo "API文档: http://<your-server-ip>:8888/docs"
echo ""
echo "查看日志: ssh $SERVER 'journalctl -u mars-sandbox -f'"
echo ""
