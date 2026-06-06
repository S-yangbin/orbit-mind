# 系统架构设计

## 概述

本项目是一个基于 WebSocket 长连接的**私有化家庭 AI 中枢系统**。通过 Hermes Agent（AI 助手）作为交互入口，用户可通过钉钉、微信等即时通讯工具，向家庭 Linux 服务器发送远程命令并获取执行结果。

## 核心设计理念

- **实时通信**：WebSocket 长连接实现毫秒级命令响应，无需轮询
- **安全可控**：命令黑白名单、超时保护、审计日志，防止危险操作
- **内网穿透**：家庭服务器无公网 IP，通过 WebSocket 客户端主动连接实现通信
- **可扩展性**：支持多节点接入，心跳机制实现节点状态实时感知

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户（钉钉/微信）                            │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ 自然语言指令
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Hermes Agent（云端 AI 助手）                        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              home-hub Skill (SKILL.md)                         │  │
│  │  ┌─────────────────┐                    ┌──────────────┐      │  │
│  │  │ send_command.py │                    │ list_nodes.py│      │  │
│  │  └────────┬────────┘                    └──────┬───────┘      │  │
│  └───────────┼─────────────────────────────────────┼──────────────┘  │
└──────────────┼─────────────────────────────────────┼───────────────┘
               │ HTTP API                            │ HTTP API
               ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  mars-sandbox (WebSocket + HTTP API)                  │
│                     ws://<your-server-ip>:8888                          │
│                                                                      │
│   功能模块：                                                           │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐          │
│   │ WebSocket 服务│  │ HTTP API 服务│  │  连接池管理       │          │
│   │ /ws/agent/   │  │ /api/commands│  │  Map<node_id,ws> │          │
│   │ /api/nodes   │  │ /api/nodes   │  │  心跳检测         │          │
│   └──────────────┘  └──────────────┘  └──────────────────┘          │
└───────────────┬───────────────────────────────┬─────────────────────┘
                │ WebSocket 长连接               │ HTTP API
                ▼                               ▼
┌─────────────────────────────────┐    ┌────────────────────────┐
│    Home Agent (WebSocket客户端)  │    │  Hermes Skill 脚本     │
│  ┌──────────────────────────┐  │    │  list_nodes.py         │
│  │ ws_client.py             │  │    └────────────────────────┘
│  │ - 节点注册               │  │
│  │ - 心跳保活               │  │
│  │ - 命令接收               │  │
│  │ - 结果发送               │  │
│  └──────────┬───────────────┘  │
│  ┌──────────┴───────────────┐  │
│  │ security.py              │  │
│  │ command_executor.py      │  │
│  │ command_logger.py        │  │
│  └──────────────────────────┘  │
└──────────────┬─────────────────┘
               │ subprocess
               ▼
┌────────────────┐
│  Linux 系统命令  │
│  (subprocess)   │
└────────────────┘
```

## 组件说明

### Hermes Agent（云端）

| 属性 | 值 |
|------|-----|
| 部署位置 | 阿里云 ECS (`<your-server-ip>`) |
| 运行方式 | Hermes Agent 守护进程 |
| 交互方式 | 钉钉/微信 Gateway |
| Skill 路径 | `~/.hermes/skills/smart-home/home-hub/` |

Hermes Agent 是 AI 助手服务，负责理解用户自然语言指令，调用 `home-hub` Skill 中的脚本完成远程控制操作。

**Skill 脚本：**

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `send_command.py` | 发送命令并等待结果 | node_id + 命令字符串 + timeout | JSON 执行结果 |
| `list_nodes.py` | 查询在线节点 | stale 阈值 | JSON 节点列表 |

### Home Agent（家庭服务器）

| 属性 | 值 |
|------|-----|
| 部署位置 | 家庭服务器 (`192.168.31.127`) |
| 运行方式 | systemd 守护进程 |
| 安装路径 | `/home/syb/orbit-mind/` |
| 配置文件 | `config.yaml` 或 `~/configs/home-agent.yaml` |

Home Agent 是长驻守护进程，通过 WebSocket 连接 mars-sandbox，接收命令并执行 shell 命令，将结果通过 WebSocket 返回。

**模块结构：**

| 模块 | 职责 |
|------|------|
| `main.py` | 主入口，异步模式，信号处理 |
| `ws_client.py` | WebSocket 客户端（连接/注册/心跳/消息收发） |
| `config.py` | 配置加载（YAML + 环境变量） |
| `security.py` | 命令黑白名单校验 |
| `command_executor.py` | 命令执行引擎（subprocess + 超时） |
| `command_logger.py` | 审计日志持久化（JSONL） |

### mars-sandbox

| 属性 | 值 |
|------|-----|
| 服务 | mars-sandbox (FastAPI + websockets + MySQL) |
| 地址 | `ws://<your-server-ip>:8888` (WebSocket) |
| HTTP API | `http://<your-server-ip>:8888/api/*` |
| 功能 | WebSocket 服务端 + 节点管理 + 命令转发 |
| SDK | websockets >= 12.0, FastAPI, SQLAlchemy |

## WebSocket 架构设计

系统采用 WebSocket 长连接架构，Home Agent 作为客户端主动连接 mars-sandbox 服务端：

| 消息类型 | 流向 | 说明 |
|----------|------|------|
| `register` | Home Agent → mars-sandbox | 节点注册 |
| `register_ack` | mars-sandbox → Home Agent | 注册确认 |
| `heartbeat` | Home Agent → mars-sandbox | 心跳保活 |
| `heartbeat_ack` | mars-sandbox → Home Agent | 心跳确认 |
| `command` | mars-sandbox → Home Agent | 命令下发 |
| `result` | Home Agent → mars-sandbox | 结果上报 |
| `error` | 双向 | 错误通知 |

### 连接管理

**连接建立流程：**

```
Home Agent                          mars-sandbox
    │                                  │
    │  WebSocket 连接                   │
    │  /ws/agent/{node_id}?secret=xxx  │
    │─────────────────────────────────>│
    │                                  │
    │  RegisterMessage                 │
    │─────────────────────────────────>│
    │                                  │ 验证节点信息
    │  RegisterAckMessage              │
    │<─────────────────────────────────│
    │                                  │
    │  HeartbeatMessage (定期)          │
    │─────────────────────────────────>│
    │  HeartbeatAckMessage             │
    │<─────────────────────────────────│
    │                                  │
    │  CommandMessage                  │
    │<─────────────────────────────────│
    │  执行命令                         │
    │  ResultMessage                   │
    │─────────────────────────────────>│
```

### 命令转发流程

```
Hermes Skill                    mars-sandbox                    Home Agent
    │                              │                                │
    │  POST /api/commands          │                                │
    │─────────────────────────────>│                                │
    │  {node_id, command, timeout} │                                │
    │                              │  查找节点 WebSocket 连接        │
    │                              │  CommandMessage                │
    │                              │───────────────────────────────>│
    │                              │                                │
    │                              │                        执行命令 │
    │                              │                                │
    │                              │  ResultMessage                 │
    │                              │<───────────────────────────────│
    │  同步等待结果                 │                                │
    │<─────────────────────────────│                                │
    │  JSON 结果                   │                                │
```

## 消息流转时序

### 命令执行流程

```
用户(钉钉)      Hermes Agent       mars-sandbox        Home Agent
    │               │                  │                   │
    │ "查看磁盘"    │                  │                   │
    │──────────────>│                  │                   │
    │               │                  │                   │
    │               │ POST /api/commands                   │
    │               │─────────────────>│                   │
    │               │                  │  CommandMessage   │
    │               │                  │──────────────────>│
    │               │                  │                   │
    │               │                  │          安全校验 │
    │               │                  │          执行命令 │
    │               │                  │                   │
    │               │                  │  ResultMessage    │
    │               │                  │<──────────────────│
    │               │  JSON 结果       │                   │
    │               │<─────────────────│                   │
    │               │                  │                   │
    │  "磁盘使用50%" │                  │                   │
    │<──────────────│                  │                   │
```

### 心跳与节点状态管理

```
Home Agent                  mars-sandbox API          list_nodes.py
    │                          │                         │
    │ WebSocket Heartbeat      │                         │
    │ (每 60 秒)               │                         │
    │─────────────────────────>│                         │
    │ 更新节点在线状态          │                         │
    │                          │                         │
    │                          │ GET /api/nodes          │
    │                          │<────────────────────────│
    │                          │  节点列表 JSON          │
    │                          │────────────────────────>│
    │                          │  输出在线节点列表        │
```

## 安全设计

### 命令安全校验

采用 **白名单优先 + 黑名单兜底** 双层校验机制：

```
命令输入
    │
    ├── 配置了白名单？
    │   ├── 是 → 命令前缀匹配白名单？
    │   │       ├── 是 → ✅ 允许执行
    │   │       └── 否 → ❌ 拒绝
    │   └── 否 → 命令匹配黑名单？
    │           ├── 是 → ❌ 拒绝
    │           └── 否 → ✅ 允许执行
```

**默认黑名单：**

```
rm -rf /
rm -rf /*
mkfs
dd if=/dev/zero of=/dev
:(){ :|:& };:
```

### 超时保护

- 命令默认超时：30 秒
- 最大允许超时：120 秒（可在 config.yaml 调整）
- 超时后自动终止进程，返回 `exit_code=-1`

### 输出截断

| 输出流 | 截断阈值 | 说明 |
|--------|----------|------|
| stdout | 64,000 字符 | 保留末尾内容 |
| stderr | 16,000 字符 | 保留末尾内容 |

### systemd 安全加固

```ini
NoNewPrivileges=true      # 禁止提权
ProtectSystem=strict      # 文件系统只读（除 ReadWritePaths）
ProtectHome=read-only     # 家目录只读
ReadWritePaths=.../logs   # 仅允许写入日志目录
PrivateTmp=true           # 隔离临时目录
```

## 配置管理

### 配置优先级

```
环境变量 > 配置文件 > 默认值
```

### 配置文件搜索路径

按顺序查找，使用第一个存在的：

1. `./config.yaml`
2. `./config.yml`
3. `~/configs/home-agent.yaml`
4. `~/.config/orbit-mind/config.yaml`

### 环境变量

| 变量 | 说明 | 优先级 |
|------|------|--------|
| `HOME_AGENT_NODE_ID` | 节点标识 | 覆盖文件 |
| `MARS_SANDBOX_URL` | mars-sandbox WebSocket 地址 | 覆盖文件 |
| `HOME_AGENT_NODE_SECRET` | 节点密钥（WebSocket 连接认证） | 覆盖文件 |
| `MARS_SANDBOX_API_KEY` | mars-sandbox API Key | 覆盖文件 |

## 项目目录结构

```
orbit-mind/
├── doc/                            # 文档
│   ├── architecture.md             # 本文档
│   ├── message-protocol.md         # 消息协议规范
│   ├── deployment.md               # 部署指南
│   └── development.md              # 开发与扩展指南
├── shared/                         # 共享模块
│   ├── __init__.py
│   └── message_protocol.py         # 消息类型定义
├── home-agent/                     # 家庭服务器守护进程
│   ├── main.py                     # 主入口（异步模式）
│   ├── config.py                   # 配置管理
│   ├── ws_client.py                # WebSocket 客户端
│   ├── security.py                 # 安全校验
│   ├── command_executor.py         # 命令执行引擎
│   ├── command_logger.py           # 审计日志
│   ├── home-agent.service          # systemd service 文件
│   ├── install.sh                  # 一键安装脚本
│   └── requirements.txt            # Python 依赖
├── home-agent-skill/               # Hermes Agent Skill
│   └── home-hub/
│       ├── SKILL.md                # Skill 定义文件
│       └── scripts/
│           ├── send_command.py     # 发送命令并等待结果
│           └── list_nodes.py       # 节点查询脚本
├── mars-sandbox/                   # 节点管理服务
│   ├── backend/                    # FastAPI 后端
│   └── frontend/                   # React 前端
└── config.example.yaml             # 配置示例
```

## 技术栈

| 层级 | 技术 |
|------|------|
| AI Agent 框架 | Hermes Agent v0.14.0 |
| 节点管理 | mars-sandbox (FastAPI + websockets + SQLAlchemy + MySQL) |
| WebSocket 通信 | websockets >= 12.0, aiohttp >= 3.9.0 |
| 配置解析 | PyYAML >= 6.0 |
| HTTP 请求 | requests >= 2.28.0 |
| 进程管理 | systemd |
| 日志采集 | journalctl |
| 语言 | Python 3.x |
| 部署 | 阿里云 ECS + 家庭 Linux 服务器 |
