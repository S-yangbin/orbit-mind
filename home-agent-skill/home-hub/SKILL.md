---
name: home-hub
description: 远程控制家庭 Linux 服务器，通过 mars-sandbox WebSocket 架构发送命令并获取执行结果
version: 2.0.0
author: syb
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [automation, remote-control, home-server, websocket]
    category: smart-home
    requires_toolsets: [terminal]
required_environment_variables:
  - name: MARS_SANDBOX_URL
    prompt: mars-sandbox 服务地址（如 http://8.213.135.161:8888）
    help: mars-sandbox 服务的 HTTP API 地址
    required_for: 发送命令到家庭服务器
  - name: MARS_SANDBOX_API_KEY
    prompt: mars-sandbox API Key
    help: 在 mars-sandbox 管理后台获取
    required_for: API 认证
---

# Home Hub - 家庭服务器远程控制 (WebSocket 架构)

通过 mars-sandbox 向家庭 Linux 服务器发送命令并获取执行结果。home-agent 通过 WebSocket 长连接接收命令。

## 何时使用

当用户需要：
- 在家庭 Linux 服务器上执行命令
- 查看家庭服务器的状态（磁盘、内存、进程等）
- 控制家庭服务器上的服务（启动/停止/重启）
- 在家庭服务器上运行脚本或程序
- 管理智能家居设备的 CLI 命令

触发关键词：家庭服务器、home server、远程命令、家里执行、家里的机器

## 快速参考

| 操作 | 命令 |
|------|------|
| 发送命令并等待结果 | `python scripts/send_command.py <node_id> "your_command" --timeout 30` |
| 查询在线节点 | `python scripts/list_nodes.py` |

## 操作流程

### 步骤 1：发送命令并获取结果

使用终端执行 send_command.py 脚本，将命令发送到 mars-sandbox，由 home-agent 执行并返回结果：

```bash
cd ~/.hermes/skills/smart-home/home-hub
python scripts/send_command.py "home-server-01" "ls -la /home" --timeout 30
```

脚本会同步等待命令执行完成，并输出：
- 节点 ID
- 执行的命令
- 退出码（0 表示成功）
- 标准输出和标准错误
- 执行耗时

### 步骤 2：向用户反馈

将执行结果整理后返回给用户。如果命令执行失败（exit_code != 0），告知用户错误原因。

## 常见用例

### 查看服务器状态
```bash
python scripts/send_command.py "home-server-01" "uname -a && df -h && free -h" --timeout 15
```

### 管理服务
```bash
python scripts/send_command.py "home-server-01" "systemctl status docker" --timeout 10
python scripts/send_command.py "home-server-01" "systemctl restart nginx" --timeout 30
```

### 执行长时间任务（增加超时）
```bash
python scripts/send_command.py "home-server-01" "docker pull nginx:latest" --timeout 120
```

### 查询在线节点
```bash
python scripts/list_nodes.py
```

## 架构说明

```
Hermes → mars-sandbox (HTTP API) → WebSocket → home-agent → 执行命令
                                    ↓
                              返回执行结果
```

- **mars-sandbox**: 作为中枢管理节点和转发命令
- **WebSocket**: home-agent 通过长连接实时接收命令
- **同步响应**: 命令执行完成后直接返回结果，无需轮询

## 环境变量配置

使用前需要设置以下环境变量：

```bash
export MARS_SANDBOX_URL="http://8.213.135.161:8888"
export MARS_SANDBOX_API_KEY="your-api-key"
```

## 错误处理

- 如果节点离线，会返回错误提示
- 如果命令执行超时，会返回超时错误
- 如果命令被安全策略拦截，会返回拦截原因
- 网络异常时会提示重试
