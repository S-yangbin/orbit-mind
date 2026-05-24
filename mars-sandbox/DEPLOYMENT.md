# Mars Sandbox WebSocket 部署指南

## 概述

Mars Sandbox现在支持WebSocket,作为home-agent的集中管理网关。

## 架构

```
home-agent (WebSocket客户端) → mars-sandbox (WebSocket服务端) ← Hermes (HTTP API)
```

## 部署步骤

### 1. 服务器准备

```bash
# SSH到服务器
ssh root@8.213.135.161

# 创建目录
mkdir -p /opt/mars-sandbox
cd /opt/mars-sandbox

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
```

### 2. 部署代码

#### 方式A: 使用部署脚本(推荐)

```bash
cd /Users/syb/workspace/orbit-mind/mars-sandbox
chmod +x deploy.sh
./deploy.sh
```

#### 方式B: 手动部署

```bash
# 从本地上传代码
cd /Users/syb/workspace/orbit-mind/mars-sandbox/backend
tar -czf ../mars-sandbox.tar.gz app/ requirements.txt
scp mars-sandbox.tar.gz root@8.213.135.161:/opt/mars-sandbox/

# 在服务器上解压
ssh root@8.213.135.161
cd /opt/mars-sandbox
tar -xzf mars-sandbox.tar.gz
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cd /opt/mars-sandbox
cp .env.example .env
nano .env
```

关键配置项:
```env
NODE_API_KEY=your-secret-key-here  # home-agent连接密钥
HOST=0.0.0.0
PORT=8888
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=mars_sandbox
```

### 4. 安装systemd服务

```bash
# 上传service文件
scp mars-sandbox.service root@8.213.135.161:/etc/systemd/system/

# 在服务器上
ssh root@8.213.135.161
systemctl daemon-reload
systemctl enable mars-sandbox
systemctl start mars-sandbox
systemctl status mars-sandbox
```

### 5. 验证部署

```bash
# 检查服务状态
ssh root@8.213.135.161 'systemctl status mars-sandbox'

# 查看日志
ssh root@8.213.135.161 'journalctl -u mars-sandbox -f'

# 测试健康检查
curl http://8.213.135.161:8888/health

# 查看API文档
open http://8.213.135.161:8888/docs
```

### 6. 运行测试

```bash
cd /Users/syb/workspace/orbit-mind/mars-sandbox

# 修改test_websocket.py中的NODE_API_KEY
nano test_websocket.py

# 运行测试
pip install websockets requests
python test_websocket.py
```

## home-agent配置

在home-agent服务器上:

```bash
# 编辑config.yaml
nano ~/orbit-mind/config.yaml

# 添加WebSocket配置
agent:
  mars_sandbox_url: "ws://8.213.135.161:8888"
  node_secret: "your-secret-key-here"  # 与NODE_API_KEY相同
  heartbeat_interval: 60
  node_id: "home-server-01"
```

启动home-agent:
```bash
cd ~/orbit-mind/home-agent
python main.py
```

## Hermes Skill使用

```bash
# 设置环境变量
export MARS_SANDBOX_URL="http://8.213.135.161:8888"
export MARS_SANDBOX_API_KEY="your-secret-key-here"

# 发送命令
cd ~/.hermes/skills/smart-home/home-hub
python scripts/send_command.py "home-server-01" "ls -la" --timeout 30
```

## 故障排查

### home-agent连接失败

```bash
# 检查mars-sandbox日志
ssh root@8.213.135.161 'journalctl -u mars-sandbox -n 100'

# 检查网络连通性
telnet 8.213.135.161 8888

# 检查NODE_API_KEY是否一致
# mars-sandbox: .env中的NODE_API_KEY
# home-agent: config.yaml中的node_secret
```

### 命令执行超时

```bash
# 检查节点是否在线
curl -H "X-API-Key: your-key" http://8.213.135.161:8888/api/nodes

# 检查home-agent日志
journalctl -u home-agent -f

# 增加超时时间
python scripts/send_command.py "node-id" "command" --timeout 60
```

### WebSocket连接断开

```bash
# 检查心跳间隔
# home-agent config.yaml: heartbeat_interval: 60

# 检查超时设置
# mars-sandbox连接池默认180秒无心跳标记离线

# 查看连接状态
ssh root@8.213.135.161 'journalctl -u mars-sandbox | grep "节点.*注册"'
```

## 性能优化

### 生产环境建议

1. **使用Redis缓存结果** (替代内存字典)
2. **增加负载均衡** (多实例mars-sandbox)
3. **启用HTTPS/WSS** (使用nginx反向代理)
4. **数据库优化** (连接池、索引)
5. **监控告警** (Prometheus + Grafana)

### Nginx配置(可选)

```nginx
server {
    listen 443 ssl http2;
    server_name mars-sandbox.example.com;

    ssl_certificate /etc/ssl/certs/mars-sandbox.crt;
    ssl_certificate_key /etc/ssl/private/mars-sandbox.key;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## API端点

- **WebSocket**: `ws://8.213.135.161:8888/ws/agent/{node_id}?secret={key}`
- **命令执行**: `POST /api/commands`
- **节点列表**: `GET /api/nodes`
- **心跳上报**: `PUT /api/nodes/heartbeat`
- **健康检查**: `GET /health`
- **API文档**: `GET /docs`

## 更新服务

```bash
# 使用部署脚本更新
./deploy.sh

# 或手动更新
ssh root@8.213.135.161
cd /opt/mars-sandbox
systemctl stop mars-sandbox
tar -xzf mars-sandbox.tar.gz
source venv/bin/activate
pip install -r requirements.txt
systemctl start mars-sandbox
```

## 安全注意事项

1. **修改默认NODE_API_KEY**
2. **启用防火墙规则** (仅开放必要端口)
3. **定期更新依赖**
4. **监控异常连接**
5. **备份数据库**
