# 部署与运维指南

## 环境要求

| 组件 | 要求 |
|------|------|
| Python | 3.8+ |
| 操作系统 | Linux (Ubuntu/Debian/CentOS) |
| 阿里云 MNS | 已创建轻量消息队列 |
| 阿里云 AccessKey | 拥有 MNS 读写权限 |

## 前置准备

### 1. 创建阿里云 MNS 队列

1. 登录 [阿里云轻量消息队列控制台](https://mns.console.aliyun.com/)
2. 创建队列，记录以下信息：
   - Endpoint（如 `https://xxx.mns.cn-qingdao.aliyuncs.com`）
   - 队列名称（如 `mate-notify`）

### 2. 获取阿里云 AccessKey

1. 登录 [阿里云 AccessKey 管理](https://ram.console.aliyun.com/manage/ak)
2. 建议使用 RAM 子账号，仅授予 MNS 权限
3. 记录 `AccessKey ID` 和 `AccessKey Secret`

---

## 部署 mars-sandbox（节点管理服务）

### 目标机器

与 Hermes Agent 同一台服务器 `root@8.213.135.161`，监听端口 8888。

> **重要**：MySQL 数据库配置了 IP 白名单，仅 `8.213.135.161` 可连接。

### 步骤 1：传输代码

```bash
scp -r mars-sandbox/ root@8.213.135.161:~/mars-sandbox/
```

### 步骤 2：安装依赖

```bash
ssh root@8.213.135.161
cd ~/mars-sandbox/backend
pip3 install -r requirements.txt
```

### 步骤 3：配置 .env

确保 `backend/.env` 中包含 `NODE_API_KEY`：

```ini
# Node management (home-agent heartbeat API key)
NODE_API_KEY=<your-node-api-key>
```

### 步骤 4：启动服务

```bash
cd ~/mars-sandbox/backend
PORT=8888 uvicorn app.main:app --host 0.0.0.0 --port 8888
```

或使用 systemd/Supervisor 管理。启动时会自动创建 `nodes` 表。

### 步骤 5：验证 API

```bash
curl http://localhost:8888/api/nodes \
  -H "X-API-Key: <your-node-api-key>"
```

应返回空节点列表。

---

## 部署 Home Agent（家庭服务器）

### 目标机器

家庭 Linux 服务器，无需公网 IP。

### 步骤 1：传输代码

```bash
# 在本地打包
cd orbit-mind
tar czf orbit-mind.tar.gz \
  shared/ home-agent/ config.example.yaml

# 传输到家庭服务器
scp orbit-mind.tar.gz syb@192.168.31.127:~/

# 在家庭服务器上解压
ssh syb@192.168.31.127
mkdir -p ~/orbit-mind
tar xzf ~/orbit-mind.tar.gz -C ~/orbit-mind/
```

### 步骤 2：安装依赖

```bash
cd ~/orbit-mind
pip3 install -r home-agent/requirements.txt
```

### 步骤 3：创建配置文件

```bash
cp ~/orbit-mind/config.example.yaml ~/orbit-mind/home-agent/config.yaml
```

编辑 `config.yaml`，填入真实值：

```yaml
mns:
  endpoint: "https://1269672658042534.mns.cn-qingdao.aliyuncs.com"
  access_key_id: "your-ak-id"
  access_key_secret: "your-ak-secret"
  queue_name: "mate-notify"

agent:
  node_id: "home-server-01"    # 节点标识（可选，默认用 hostname）
  max_timeout: 120
  allowed_commands: []          # 空则不限制
  blocked_commands:
    - "rm -rf /"
    - "rm -rf /*"
    - "mkfs"
    - "dd if=/dev/zero of=/dev"
    - ":(){ :|:& };:"
  working_dir: "~"
  log_file: null
  audit_log_dir: null           # 默认 ~/orbit-mind/logs/
```

### 步骤 4：手动测试

```bash
cd ~/orbit-mind
python3 home-agent/main.py -c home-agent/config.yaml
```

看到以下日志说明启动成功：

```
Home Agent 启动
节点 ID: home-server-01
MNS 队列: mate-notify
工作目录: /home/syb
最大超时: 120s
```

`Ctrl+C` 停止后，继续配置 systemd。

### 步骤 5：配置 systemd 服务

#### 方式 A：使用安装脚本（推荐）

```bash
sudo bash ~/orbit-mind/home-agent/install.sh
```

脚本会自动完成：
1. 安装 Python 依赖
2. 创建日志目录
3. 从 `config.yaml` 生成 `.env` 文件
4. 安装并启用 systemd service

#### 方式 B：手动安装

```bash
# 创建日志目录
mkdir -p ~/orbit-mind/logs

# 创建 .env 文件
cat > ~/orbit-mind/home-agent/.env << 'EOF'
MNS_ENDPOINT=https://1269672658042534.mns.cn-qingdao.aliyuncs.com
ALIBABA_CLOUD_ACCESS_KEY_ID=your-ak-id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your-ak-secret
MNS_QUEUE_NAME=mate-notify
EOF
chmod 600 ~/orbit-mind/home-agent/.env

# 安装 service 文件
sudo cp ~/orbit-mind/home-agent/home-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable home-agent
```

### 步骤 6：启动服务

```bash
sudo systemctl start home-agent
sudo systemctl status home-agent
```

---

## 部署 Hermes Skill（云端）

### 目标机器

Hermes Agent 所在的云服务器。

### 步骤 1：传输 Skill 文件

```bash
# 在本地
scp -r home-agent-skill/home-hub/ root@8.213.135.161:~/.hermes/skills/smart-home/
```

### 步骤 2：安装 Skill 依赖

```bash
ssh root@8.213.135.161
pip3 install --break-system-packages aliyun-mns-sdk
# 或使用虚拟环境：
# pip3 install aliyun-mns-sdk
```

### 步骤 3：配置环境变量

将 MNS 凭证写入 Hermes 的环境变量文件：

```bash
cat >> ~/.hermes/.env << 'EOF'
MNS_ENDPOINT=https://1269672658042534.mns.cn-qingdao.aliyuncs.com
ALIBABA_CLOUD_ACCESS_KEY_ID=your-ak-id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your-ak-secret
MNS_QUEUE_NAME=mate-notify
MARS_SANDBOX_URL=http://8.213.135.161:8888
MARS_SANDBOX_API_KEY=<your-node-api-key>
EOF
```

确保 Hermes 配置了环境变量透传：

```bash
hermes config set terminal.env_passthrough "MNS_ENDPOINT,ALIBABA_CLOUD_ACCESS_KEY_ID,ALIBABA_CLOUD_ACCESS_KEY_SECRET,MNS_QUEUE_NAME,MARS_SANDBOX_URL,MARS_SANDBOX_API_KEY"
```

### 步骤 4：重启 Hermes

```bash
hermes restart
# 或根据实际部署方式重启
```

### 步骤 5：验证 Skill

```bash
ssh root@8.213.135.161
cd ~/.hermes/skills/smart-home/home-hub

# 发送测试命令
python3 scripts/send_command.py "echo 'hello from home server'" --timeout 10
# 输出: REQUEST_ID=xxx

# 轮询结果
python3 scripts/poll_result.py "<request_id>" --max-wait 30
# 输出: {"exit_code": 0, "stdout": "hello from home server\n", ...}
```

---

## 运维命令参考

### Home Agent 服务管理

```bash
# 启动
sudo systemctl start home-agent

# 停止
sudo systemctl stop home-agent

# 重启
sudo systemctl restart home-agent

# 查看状态
sudo systemctl status home-agent

# 查看实时日志
sudo journalctl -u home-agent -f

# 查看最近 100 行日志
sudo journalctl -u home-agent -n 100 --no-pager

# 开机自启（安装时已自动启用）
sudo systemctl enable home-agent
```

### 审计日志

审计日志按天分文件存储在 `~/orbit-mind/logs/` 目录：

```bash
# 查看今天的审计日志
cat ~/orbit-mind/logs/commands-$(date +%Y-%m-%d).jsonl | python3 -m json.tool

# 查看被拦截的命令
grep '"blocked": true' ~/orbit-mind/logs/commands-*.jsonl

# 查看失败的命令
grep '"status": "failed"' ~/orbit-mind/logs/commands-*.jsonl

# 统计今日命令数
wc -l ~/orbit-mind/logs/commands-$(date +%Y-%m-%d).jsonl
```

审计日志 JSONL 格式：

```json
{
  "timestamp": "2026-05-24T10:30:01.234567+00:00",
  "request_id": "a1b2c3d4-...",
  "command": "ls -la /home",
  "exit_code": 0,
  "duration_ms": 42,
  "blocked": false,
  "block_reason": "",
  "stdout_preview": "total 24\ndrwx...",
  "stderr_preview": "",
  "status": "success"
}
```

### 节点查询

```bash
# 在 Hermes 服务器上查询在线节点
cd ~/.hermes/skills/smart-home/home-hub
python3 scripts/list_nodes.py --stale 180
```

输出示例：

```json
{
  "total": 1,
  "online": 1,
  "offline": 0,
  "nodes": [
    {
      "node_id": "home-server-01",
      "hostname": "syb-linux",
      "ip": "192.168.31.127",
      "platform": "Linux 6.8.0-40-generic",
      "version": "1.0.0",
      "uptime_seconds": 86400,
      "last_heartbeat_at": "2026-05-24T10:30:00",
      "status": "online",
      "uptime": "1d 0h 0m"
    }
  ]
}
```

---

## 故障排查

### Home Agent 无法启动

```bash
# 查看详细错误
sudo journalctl -u home-agent -n 50 --no-pager

# 常见错误：
# 1. 配置文件找不到 → 检查 -c 参数路径
# 2. MNS 认证失败 → 检查 .env 文件中的 AK/SK
# 3. 队列不存在 → 检查 MNS 控制台队列是否创建
```

### 命令执行无响应

```bash
# 1. 检查 home-agent 是否运行
sudo systemctl status home-agent

# 2. 查看最近的日志
sudo journalctl -u home-agent -n 20 --no-pager

# 3. 检查网络连接（需要能访问 MNS endpoint）
curl -s https://1269672658042534.mns.cn-qingdao.aliyuncs.com

# 4. 在 Hermes 服务器手动测试 MNS 连接
python3 scripts/send_command.py "echo test" --timeout 10
```

### 心跳不更新

```bash
# 检查 home-agent 是否运行
sudo systemctl status home-agent

# 查看心跳相关日志
sudo journalctl -u home-agent | grep -i heartbeat

# 检查 mars-sandbox 是否可访问
curl -s http://8.213.135.161:8888/health

# 重启服务让心跳重新发送
sudo systemctl restart home-agent
```

### 队列消息堆积

如果队列中有大量消息未被消费：

```bash
# 检查 home-agent 状态
sudo systemctl status home-agent

# 如果 agent 正常但消息仍堆积，可能是 re-send 循环
# 重启 agent 清理状态
sudo systemctl restart home-agent
```

---

## 更新与升级

### 更新 Home Agent

```bash
# 1. 停止服务
sudo systemctl stop home-agent

# 2. 备份当前版本
cp -r ~/orbit-mind/home-agent ~/orbit-mind/home-agent.bak

# 3. 传输新版本
scp home-agent/*.py syb@192.168.31.127:~/orbit-mind/home-agent/
scp shared/message_protocol.py syb@192.168.31.127:~/orbit-mind/shared/

# 4. 安装新依赖（如有）
pip3 install -r ~/orbit-mind/home-agent/requirements.txt

# 5. 启动服务
sudo systemctl start home-agent
```

### 更新 Hermes Skill

```bash
# 传输新版本
scp -r home-agent-skill/home-hub/* root@8.213.135.161:~/.hermes/skills/smart-home/home-hub/

# 重启 Hermes（如果需要重新加载 Skill）
hermes restart
```

---

## 安全建议

1. **使用 RAM 子账号**：不要使用主账号 AccessKey，创建专用 RAM 子账号并只授予 MNS 权限
2. **定期轮换 AK/SK**：建议每 90 天轮换一次
3. **配置白名单**：生产环境建议启用命令白名单模式
4. **审计日志监控**：定期检查 `~/orbit-mind/logs/` 中的审计日志
5. **限制 .env 权限**：确保 `.env` 文件权限为 `600`
6. **启用 systemd 安全加固**：`home-agent.service` 中已配置，不要随意移除
