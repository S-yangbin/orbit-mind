# Home Hub — 家庭服务器远程控制套件

通过 mars-cli + mars-sandbox + home-agent 三层架构，实现从任意终端（含 AI 大模型）远程操控家庭 Linux 服务器。

## 架构总览

```
AI 大模型 / 终端用户
       │
       ▼
   mars-cli  ──(HTTP)──▶  mars-sandbox  ──(WebSocket)──▶  home-agent  ──▶  执行 shell 命令
   (CLI 客户端)           (中枢网关服务)                   (节点 agent)
                         <your-server-ip>:8888               家庭 Linux 服务器
```

**组件说明：**

| 组件 | 角色 | 部署位置 | 通信协议 |
|------|------|----------|----------|
| **mars-sandbox** | 中枢网关，管理节点、转发命令、Web 管理面板 | 云服务器 (<your-server-ip>) | HTTP + WebSocket |
| **home-agent** | 节点 agent，接收命令并在本机执行 | 家庭 Linux 服务器 | WebSocket 长连接 |
| **mars-cli** | CLI 客户端，封装 mars-sandbox HTTP API | 开发机 / AI 终端 | HTTP |

---

## 前置要求

- 一台云服务器（用于运行 mars-sandbox），已部署或可 SSH 部署
- 一台或多台家庭 Linux 服务器（用于运行 home-agent）
- Python 3.9+ 环境（mars-cli 本地安装）

---

## 一、部署 mars-sandbox（中枢网关）

### 1.1 服务器初始化

```bash
# SSH 到云服务器
ssh root@<your-server-ip>

# 创建应用目录
mkdir -p /opt/mars-sandbox
cd /opt/mars-sandbox

# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 1.2 部署代码

**方式 A — 使用部署脚本（推荐）：**

在本地开发机执行：

```bash
cd /path/to/orbit-mind/mars-sandbox
chmod +x deploy.sh
./deploy.sh
```

脚本会自动：构建前端 → 打包后端 → 上传到服务器 → 安装依赖 → 启动服务。

**方式 B — 手动部署：**

```bash
# 本地：打包后端
cd orbit-mind/mars-sandbox/backend
tar -czf ../mars-sandbox-backend.tar.gz app/ requirements.txt

# 本地：构建并打包前端
cd ../frontend
pnpm install && pnpm run build
tar -czf ../mars-sandbox-frontend.tar.gz dist/

# 上传到服务器
scp ../mars-sandbox-backend.tar.gz ../mars-sandbox-frontend.tar.gz root@<your-server-ip>:/opt/mars-sandbox/

# 服务器上：解压并安装
ssh root@<your-server-ip>
cd /opt/mars-sandbox
tar -xzf mars-sandbox-backend.tar.gz
mkdir -p frontend && tar -xzf mars-sandbox-frontend.tar.gz -C frontend/
source venv/bin/activate
pip install -r requirements.txt
```

### 1.3 配置环境变量

```bash
cd /opt/mars-sandbox
cat > .env << 'EOF'
APP_NAME=mars-sandbox
APP_ENV=production
SECRET_KEY=<生成一个随机字符串>

# 数据库（MySQL 或 SQLite）
DB_TYPE=sqlite
# 如使用 MySQL：
# DB_HOST=your-mysql-host
# DB_PORT=3306
# DB_USER=your-db-user
# DB_PASSWORD=your-db-password
# DB_NAME=mars_sandbox

# Dashboard 登录凭据
AUTH_USERNAME=admin
AUTH_PASSWORD=<设置密码>

# 节点认证密钥（home-agent 和 mars-cli 共用此密钥）
NODE_API_KEY=<设置一个强密钥>

# 服务配置
HOST=0.0.0.0
PORT=8888
EOF
```

> **重要：** `NODE_API_KEY` 是核心认证凭据，home-agent 连接和 mars-cli 调用都需要它。请设置一个安全的随机字符串。

### 1.4 安装 systemd 服务

```bash
cat > /etc/systemd/system/mars-sandbox.service << 'EOF'
[Unit]
Description=Mars Sandbox - Home Agent WebSocket Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mars-sandbox
Environment="PATH=/opt/mars-sandbox/venv/bin"
ExecStart=/opt/mars-sandbox/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8888 --ws websockets
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mars-sandbox

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动
systemctl daemon-reload
systemctl enable mars-sandbox
systemctl start mars-sandbox
```

### 1.5 验证服务

```bash
# 检查服务状态
systemctl status mars-sandbox

# 健康检查
curl http://<your-server-ip>:8888/health

# 查看 API 文档
# 浏览器访问: http://<your-server-ip>:8888/docs
```

---

## 二、部署 home-agent（节点 agent）

在每台需要远程控制的家庭 Linux 服务器上执行：

### 2.1 获取代码

```bash
cd ~
git clone <your-repo-url> orbit-mind
# 或将 home-agent/ 目录拷贝到服务器
```

### 2.2 安装依赖

```bash
cd ~/orbit-mind/home-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.3 配置文件

```bash
cat > ~/orbit-mind/config.yaml << 'EOF'
agent:
  node_id: "home-server-01"           # 节点唯一标识
  mars_sandbox_url: "ws://<your-server-ip>:8888"  # mars-sandbox WebSocket 地址
  node_secret: "<与 NODE_API_KEY 相同>"         # 认证密钥
  heartbeat_interval: 60              # 心跳间隔（秒）
  reconnect_delay: 5                  # 断线重连延迟（秒）
  max_reconnect_attempts: 0           # 最大重连次数，0=无限
  max_timeout: 120                    # 命令最大超时（秒）
  working_dir: "~"                    # 命令执行工作目录
  blocked_commands:                   # 危险命令黑名单
    - "rm -rf /"
    - "rm -rf /*"
    - "mkfs"
    - "dd if=/dev/zero of=/dev"
EOF
```

### 2.4 安装 systemd 服务

```bash
cat > /etc/systemd/system/home-agent.service << 'EOF'
[Unit]
Description=Home Agent - Remote Command Executor
After=network.target

[Service]
Type=simple
User=syb
WorkingDirectory=/home/syb/orbit-mind/home-agent
ExecStart=/home/syb/orbit-mind/home-agent/.venv/bin/python main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=home-agent

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable home-agent
systemctl start home-agent
```

### 2.5 验证连接

```bash
# 检查 home-agent 日志
journalctl -u home-agent -f

# 应看到类似输出：
# WebSocket 连接成功: ws://<your-server-ip>:8888/ws/agent/home-server-01
# 心跳发送成功
```

---

## 三、安装 mars-cli（CLI 客户端）

### 3.1 安装

```bash
cd /path/to/orbit-mind/tools/mars-cli

# 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate

# 安装（开发模式）
pip install -e .

# 验证安装
mars-cli --help
```

**也可以直接 pip 安装：**

```bash
pip install /path/to/orbit-mind/tools/mars-cli
```

### 3.2 配置连接信息

mars-cli 支持三种配置方式（优先级从高到低）：

**方式 A — 配置文件（推荐）：**

```bash
mkdir -p ~/.config/mars-cli
cat > ~/.config/mars-cli/config.json << 'EOF'
{
    "url": "http://<your-server-ip>:8888",
    "api_key": "<你的 NODE_API_KEY>"
}
EOF
```

配置文件自动查找路径（按优先级）：
1. `./mars-cli.json`（当前目录）
2. `~/.config/mars-cli/config.json`（XDG 标准）
3. `~/.mars-cli.json`（home 目录简写）

**方式 B — 环境变量：**

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export MARS_SANDBOX_URL="http://<your-server-ip>:8888"
export MARS_SANDBOX_API_KEY="<你的 NODE_API_KEY>"
```

**方式 C — 命令行参数（临时使用）：**

```bash
mars-cli --url http://<your-server-ip>:8888 --api-key <KEY> nodes
```

### 3.3 验证

```bash
# 检查 mars-sandbox 连通性
mars-cli health

# 查看在线节点
mars-cli nodes

# 执行测试命令
mars-cli exec home-server-01 'echo "Hello from home-agent!"'
```

---

## 四、mars-cli 使用速查

| 命令 | 说明 |
|------|------|
| `mars-cli health` | 检查 mars-sandbox 服务状态 |
| `mars-cli nodes` | 列出所有节点及在线状态 |
| `mars-cli nodes --table` | 表格形式展示节点 |
| `mars-cli exec <node_id> '<cmd>'` | 在远程节点执行命令 |
| `mars-cli exec <node_id> '<cmd>' -t 120` | 指定超时（秒） |
| `mars-cli pages` | 查询托管页面列表 |
| `mars-cli pages -q 'keyword'` | 搜索页面 |
| `mars-cli tags` | 列出所有标签 |

---

## 五、故障排查

| 问题 | 排查步骤 |
|------|----------|
| mars-cli 报 "认证失败" | 检查 api_key 是否与服务器 NODE_API_KEY 一致 |
| 节点显示 offline | 检查 home-agent 是否运行：`journalctl -u home-agent -f` |
| 命令执行超时 | 增大 `-t` 参数；检查节点网络；查看 home-agent 日志 |
| 命令被安全策略拦截 | 检查 home-agent config.yaml 的 blocked_commands |
| mars-sandbox 不可达 | `ssh root@<your-server-ip> 'systemctl status mars-sandbox'` |

**日志查看：**

```bash
# mars-sandbox 日志
ssh root@<your-server-ip> 'journalctl -u mars-sandbox -f'

# home-agent 日志（在节点服务器上）
journalctl -u home-agent -f
```

---

## 六、更新部署

```bash
# 更新 mars-sandbox（本地执行）
cd /path/to/orbit-mind/mars-sandbox
./deploy.sh

# 更新 home-agent（在节点服务器上）
cd ~/orbit-mind
git pull
systemctl restart home-agent

# 更新 mars-cli（本地执行）
cd /path/to/orbit-mind/tools/mars-cli
pip install -e .
```
