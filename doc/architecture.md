# 系统架构设计

## 概述

本项目是一个基于阿里云轻量消息队列（MNS）的**私有化家庭 AI 中枢系统**。通过 Hermes Agent（AI 助手）作为交互入口，用户可通过钉钉、微信等即时通讯工具，向家庭 Linux 服务器发送远程命令并获取执行结果。

## 核心设计理念

- **轻量优先**：单 MNS 队列承载命令、结果、心跳三类消息，节省云资源成本
- **安全可控**：命令黑白名单、超时保护、审计日志，防止危险操作
- **去中心化**：家庭服务器无公网 IP，通过 MNS 队列实现异步通信
- **可扩展性**：支持多节点接入，心跳机制实现节点发现

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
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │  │
│  │  │ send_command.py │  │ poll_result.py  │  │ list_nodes.py│  │  │
│  │  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘  │  │
│  └───────────┼─────────────────────┼──────────────────┼──────────┘  │
└──────────────┼─────────────────────┼──────────────────┼─────────────┘
               │ command             │ result
               ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  阿里云 MNS（轻量消息队列）                              │
│                     队列: mate-notify (单队列)                         │
│                                                                      │
│   消息类型：                                                           │
│   ┌──────────┐  ┌──────────┐                                        │
│   │ command  │  │  result  │                                         │
│   └──────────┘  └──────────┘                                        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ 长轮询
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Home Agent（家庭服务器守护进程）                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
│  │  mns_client│ │  security  │ │  executor  │ │command_logger  │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │
│  ┌────────────┐ ┌────────────┐                                     │
│  │  heartbeat │ │   config   │                                     │
│  └────────────┘ └────────────┘                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                  HTTP PUT       │        │ subprocess
            /api/nodes/heartbeat  │        ▼
                                  ▼        ┌────────────────┐
┌─────────────────────────────────────┐    │  Linux 系统命令  │
│    mars-sandbox (FastAPI + MySQL)   │    │  （subprocess）  │
│    http://8.213.135.161:8888        │    └────────────────┘
│    节点注册 + 心跳持久化 + 查询      │
└─────────────────────────────────────┘
```

## 组件说明

### Hermes Agent（云端）

| 属性 | 值 |
|------|-----|
| 部署位置 | 阿里云 ECS (`8.213.135.161`) |
| 运行方式 | Hermes Agent 守护进程 |
| 交互方式 | 钉钉/微信 Gateway |
| Skill 路径 | `~/.hermes/skills/smart-home/home-hub/` |

Hermes Agent 是 AI 助手服务，负责理解用户自然语言指令，调用 `home-hub` Skill 中的脚本完成远程控制操作。

**Skill 脚本：**

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `send_command.py` | 发送命令到队列 | 命令字符串 + timeout | `REQUEST_ID=<uuid>` |
| `poll_result.py` | 轮询执行结果 | request_id + max-wait | JSON 结果 |
| `list_nodes.py` | 查询在线节点 | stale 阈值 | JSON 节点列表（来自 mars-sandbox） |

### Home Agent（家庭服务器）

| 属性 | 值 |
|------|-----|
| 部署位置 | 家庭服务器 (`192.168.31.127`) |
| 运行方式 | systemd 守护进程 |
| 安装路径 | `/home/syb/orbit-mind/` |
| 配置文件 | `config.yaml` 或 `~/configs/home-agent.yaml` |

Home Agent 是长驻守护进程，负责从 MNS 队列消费命令消息、执行 shell 命令、将结果发回队列。

**模块结构：**

| 模块 | 职责 |
|------|------|
| `main.py` | 主循环，消息分发，信号处理 |
| `mns_client.py` | MNS SDK 封装（send/receive/delete/peek） |
| `config.py` | 配置加载（YAML + 环境变量） |
| `security.py` | 命令黑白名单校验 |
| `command_executor.py` | 命令执行引擎（subprocess + 超时） |
| `command_logger.py` | 审计日志持久化（JSONL） |
| `heartbeat.py` | 心跳发送器（HTTP 上报到 mars-sandbox） |

### 阿里云 MNS

| 属性 | 值 |
|------|-----|
| 服务 | 阿里云轻量消息队列（原 MNS） |
| Endpoint | `https://1269672658042534.mns.cn-qingdao.aliyuncs.com` |
| 队列名称 | `mate-notify` |
| 队列数量 | **1**（单队列模式，节省成本） |
| SDK | `aliyun-mns-sdk` (Python) |

## 单队列设计

出于成本考虑（阿里云队列按数量计费），系统只使用 **1 个 MNS 队列** 承载两类消息：

| 消息类型 | 流向 | 说明 |
|----------|------|------|
| `command` | Hermes → Home Agent | 命令请求 |
| `result` | Home Agent → Hermes | 执行结果 |

> **注意**：节点心跳已迁移到 mars-sandbox HTTP API，不再占用 MNS 队列资源。

### 消息路由策略

单队列的核心挑战是：home-agent 会收到自己发出的 result 和 heartbeat 消息。

**解决方案：Re-send + Delete 模式**

```
home-agent 收到消息
    │
    ├── type=command  → 执行命令 → 发送 result → 删除原消息
    │
    ├── type=result   → re-send 回队列 → 删除原消息
    │                    （result 是给 Hermes 的，不是给 home-agent）
    │
    └── 未知类型 → 直接删除
```

## 消息流转时序

### 命令执行流程

```
用户(钉钉)      Hermes Agent       MNS Queue        Home Agent
    │               │                  │                 │
    │ "查看磁盘"    │                  │                 │
    │──────────────>│                  │                 │
    │               │                  │                 │
    │               │ send_command.py  │                 │
    │               │─────────────────>│                 │
    │               │ REQUEST_ID=xxx   │                 │
    │               │<─────────────────│                 │
    │               │                  │                 │
    │               │ poll_result.py   │                 │
    │               │─────────────────>│                 │
    │               │                  │                 │
    │               │                  │  receive(30s)   │
    │               │                  │────────────────>│
    │               │                  │   command msg   │
    │               │                  │<────────────────│
    │               │                  │                 │
    │               │                  │          安全校验│
    │               │                  │          执行命令│
    │               │                  │                 │
    │               │                  │  send(result)   │
    │               │                  │<────────────────│
    │               │                  │                 │
    │               │  receive(result) │                 │
    │               │<─────────────────│                 │
    │               │  delete          │                 │
    │               │─────────────────>│                 │
    │               │                  │                 │
    │  "磁盘使用50%" │                  │                 │
    │<──────────────│                  │                 │
```

### 心跳与节点发现

```
Home Agent                  mars-sandbox API          list_nodes.py
    │                          │                         │
    │ PUT /api/nodes/heartbeat │                         │
    │─────────────────────────>│                         │
    │  {"status": "ok"}        │                         │
    │<─────────────────────────│                         │
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
| `MNS_ENDPOINT` | MNS 服务端点 | 覆盖文件 |
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | 阿里云 AK | 覆盖文件 |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | 阿里云 SK | 覆盖文件 |
| `MNS_QUEUE_NAME` | 队列名称 | 覆盖文件 |
| `HOME_AGENT_NODE_ID` | 节点标识 | 覆盖文件 |
| `MARS_SANDBOX_URL` | mars-sandbox API 地址 | 覆盖文件 |
| `MARS_SANDBOX_API_KEY` | 节点心跳 API Key | 覆盖文件 |

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
│   ├── main.py                     # 主入口
│   ├── config.py                   # 配置管理
│   ├── mns_client.py               # MNS 客户端封装
│   ├── security.py                 # 安全校验
│   ├── command_executor.py         # 命令执行引擎
│   ├── command_logger.py           # 审计日志
│   ├── heartbeat.py                # 心跳发送器（HTTP → mars-sandbox）
│   ├── home-agent.service          # systemd service 文件
│   ├── install.sh                  # 一键安装脚本
│   └── requirements.txt            # Python 依赖
├── home-agent-skill/               # Hermes Agent Skill
│   └── home-hub/
│       ├── SKILL.md                # Skill 定义文件
│       └── scripts/
│           ├── send_command.py     # 发送命令脚本
│           ├── poll_result.py      # 轮询结果脚本
│           └── list_nodes.py       # 节点查询脚本
└── config.example.yaml             # 配置示例
```

## 技术栈

| 层级 | 技术 |
|------|------|
| AI Agent 框架 | Hermes Agent v0.14.0 |
| 节点管理 | mars-sandbox (FastAPI + SQLAlchemy + MySQL) |
| 消息队列 | 阿里云轻量消息队列 (MNS) |
| 消息 SDK | aliyun-mns-sdk >= 1.3.0 |
| 配置解析 | PyYAML >= 6.0 |
| 进程管理 | systemd |
| 日志采集 | journalctl |
| 语言 | Python 3.x |
| 部署 | 阿里云 ECS + 家庭 Linux 服务器 |
