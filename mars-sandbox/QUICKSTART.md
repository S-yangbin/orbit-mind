# WebSocket 快速开始

## 5分钟测试WebSocket功能

### 步骤 1: 部署mars-sandbox到服务器

```bash
cd /Users/syb/workspace/orbit-mind/mars-sandbox

# 1. 修改.env配置
cp backend/.env.example backend/.env
nano backend/.env
# 修改: NODE_API_KEY=test-secret-key-123

# 2. 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 步骤 2: 配置home-agent

```bash
cd /Users/syb/workspace/orbit-mind

# 编辑配置
nano config.yaml

# 添加:
agent:
  mars_sandbox_url: "ws://<your-server-ip>:8888"
  node_secret: "test-secret-key-123"
  node_id: "test-node-001"
  heartbeat_interval: 60
```

### 步骤 3: 启动home-agent

```bash
cd home-agent

# 安装依赖
pip install -r requirements.txt

# 启动
python main.py
```

你应该看到:
```
============================================
Home Agent 启动 (WebSocket 架构)
节点 ID: test-node-001
mars-sandbox: ws://<your-server-ip>:8888
...
============================================
正在连接 mars-sandbox: ws://<your-server-ip>:8888
WebSocket 连接成功
已发送注册消息
节点注册成功: test-node-001
心跳循环已启动: interval=60s
开始监听消息...
```

### 步骤 4: 测试命令执行

在另一个终端:

```bash
cd /Users/syb/workspace/orbit-mind/home-agent-skill/home-hub/scripts

# 设置环境变量
export MARS_SANDBOX_URL="http://<your-server-ip>:8888"
export MARS_SANDBOX_API_KEY="test-secret-key-123"

# 发送测试命令
python send_command.py "test-node-001" "echo Hello WebSocket" --timeout 10
```

你应该看到:
```
正在发送命令到节点 test-node-001...

============================================================
节点: test-node-001
命令: echo Hello WebSocket
退出码: 0
耗时: 15ms
============================================================

[标准输出]
Hello WebSocket
```

### 步骤 5: 查看节点状态

```bash
# 查询在线节点
python list_nodes.py

# 或直接访问API
curl -H "X-API-Key: test-secret-key-123" \
  http://<your-server-ip>:8888/api/nodes | jq
```

## 完整测试流程

```bash
# 运行自动化测试
cd /Users/syb/workspace/orbit-mind/mars-sandbox
pip install websockets requests
python test_websocket.py
```

## 常见问题

### Q: home-agent连接失败?

A: 检查以下几点:
1. NODE_API_KEY是否一致(mars-sandbox的.env和home-agent的config.yaml)
2. 服务器8888端口是否开放
3. mars-sandbox服务是否运行: `systemctl status mars-sandbox`

### Q: 命令执行超时?

A: 检查:
1. home-agent是否在线: `curl /api/nodes`
2. home-agent日志: `journalctl -u home-agent -f`
3. 增加timeout参数: `--timeout 30`

### Q: 如何查看日志?

```bash
# mars-sandbox日志
ssh root@<your-server-ip> 'journalctl -u mars-sandbox -f'

# home-agent日志
journalctl -u home-agent -f
```

## 下一步

- 阅读 [DEPLOYMENT.md](DEPLOYMENT.md) 了解完整部署流程
- 查看 [API文档](http://<your-server-ip>:8888/docs)
- 配置Hermes Skill实现IM控制
- 集成EPD Tool控制电子墨水屏

## 架构说明

```
你的IM → Hermes AI → mars-sandbox (HTTP API)
                            ↓ WebSocket
                      home-agent (执行命令)
                            ↓
                      你的Linux服务器
```

**优势:**
- ✅ 实时通信 (毫秒级)
- ✅ 自动重连
- ✅ 心跳保活
- ✅ 集中管理
- ✅ 无需MNS队列
