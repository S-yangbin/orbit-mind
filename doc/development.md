# 开发与扩展指南

## 本地开发环境

### 克隆项目

```bash
git clone <repo-url> orbit-mind
cd orbit-mind
```

### 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r home-agent/requirements.txt
```

### 目录说明

```
orbit-mind/
├── shared/                 # 共享模块（消息协议）
│   └── message_protocol.py # 所有消息类型定义
├── home-agent/             # 家庭服务器守护进程
│   └── *.py                # 各功能模块
├── home-agent-skill/       # Hermes Agent Skill
│   └── home-hub/
│       ├── SKILL.md        # Skill 定义
│       └── scripts/        # CLI 脚本
└── config.example.yaml     # 配置示例
```

---

## 核心模块详解

### message_protocol.py（共享消息协议）

位置：`shared/message_protocol.py`

定义所有消息类型的数据类，均支持 JSON 序列化/反序列化。

```python
from shared.message_protocol import (
    RegisterMessage,      # 节点注册消息
    RegisterAckMessage,   # 注册确认消息
    HeartbeatMessage,     # 心跳消息
    HeartbeatAckMessage,  # 心跳确认消息
    CommandMessage,       # 命令消息
    ResultMessage,        # 结果消息
    ErrorMessage,         # 错误消息
    parse_message,        # 解析 JSON → dict
)

# 创建命令消息
cmd = CommandMessage(command="ls -la", timeout=30, request_id="uuid")
json_str = cmd.to_json()

# 从 JSON 恢复
cmd2 = CommandMessage.from_json(json_str)

# 解析消息类型
data = parse_message(json_str)
msg_type = data.get("type")
if msg_type == "command":
    print("这是一条命令")
```

**扩展新消息类型**：

1. 在 `message_protocol.py` 添加新的 `@dataclass` 类
2. 实现 `to_json()` 和 `from_dict()` 方法
3. 在 WebSocket 消息处理中添加路由分支

### ws_client.py（WebSocket 客户端）

位置：`home-agent/ws_client.py`

封装 WebSocket 连接管理，提供节点注册、心跳保活、命令接收和结果发送功能。

```python
from ws_client import WebSocketClient
from shared.message_protocol import CommandMessage, ResultMessage

client = WebSocketClient(
    server_url="ws://localhost:8888",
    node_id="home-server-01",
    node_secret="your-secret",
    heartbeat_interval=60,
    reconnect_delay=5,
    max_reconnect_attempts=0,  # 0 表示无限重试
)

# 设置命令处理器
async def handle_command(cmd_msg: CommandMessage) -> ResultMessage:
    # 执行命令逻辑
    result = execute_command(cmd_msg.command, cmd_msg.timeout)
    return ResultMessage(
        request_id=cmd_msg.request_id,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_ms=result.duration_ms,
    )

client.set_command_handler(handle_command)

# 运行客户端（自动重连）
await client.run_with_reconnect()
```

**关键设计：自动重连机制**

WebSocket 客户端内置指数退避重连策略：
1. 初始延迟 5 秒，每次翻倍
2. 最大延迟 60 秒
3. 支持配置最大重连次数

这保证了网络不稳定时自动恢复连接。

### security.py（安全校验）

位置：`home-agent/security.py`

```python
from security import check_command

blocked = ["rm -rf /", "mkfs"]
allowed = []  # 空则不启用白名单

ok, reason = check_command("ls -la", blocked, allowed)
# → (True, "通过")

ok, reason = check_command("rm -rf /", blocked, allowed)
# → (False, "命令被安全策略拦截 (匹配黑名单: rm -rf /)")

# 白名单模式
allowed = ["systemctl ", "docker ", "ls "]
ok, reason = check_command("systemctl status nginx", blocked, allowed)
# → (True, "白名单通过")

ok, reason = check_command("cat /etc/passwd", blocked, allowed)
# → (False, "命令不在白名单内: cat /etc/passwd")
```

### command_executor.py（命令执行引擎）

位置：`home-agent/command_executor.py`

使用 `subprocess.run` 执行 shell 命令，支持超时保护和输出截断。

```python
from command_executor import execute_command

result = execute_command(
    command="ls -la /home",
    timeout=30,
    working_dir="/home/syb",
    max_timeout=120,
)

print(result.exit_code)    # 0
print(result.stdout)       # "total 24\ndrwx..."
print(result.stderr)       # ""
print(result.duration_ms)  # 42
```

### command_logger.py（审计日志）

位置：`home-agent/command_logger.py`

```python
from command_logger import AuditLogger

logger = AuditLogger(log_dir="~/orbit-mind/logs")

logger.log_command(
    request_id="xxx",
    command="ls -la",
    exit_code=0,
    duration_ms=42,
    blocked=False,
    stdout_preview="total 24...",
    stderr_preview="",
)
# 写入: ~/orbit-mind/logs/commands-2026-05-24.jsonl
```

日志按天分文件，JSONL 格式（每行一条 JSON 记录）。

### main.py（主入口）

位置：`home-agent/main.py`

异步模式主程序，集成 WebSocket 客户端、命令执行器和安全校验。

```python
import asyncio
from main import run_home_agent
from config import load_config

# 加载配置
config = load_config("config.yaml")

# 运行 home-agent（异步）
asyncio.run(run_home_agent(config))
```

---

## 添加新功能

### 示例：添加新功能

#### 1. 在 ws_client.py 中添加消息处理

在 `listen()` 方法中添加新的消息类型处理：

```python
async def listen(self):
    async for message in self.websocket:
        data = json.loads(message)
        msg_type = data.get("type")
        
        if msg_type == "command":
            await self._handle_command(data)
        elif msg_type == "file_upload":  # 新增
            await self._handle_file_upload(data)  # 新增
        elif msg_type == "heartbeat_ack":
            logger.debug("收到心跳确认")
```

#### 2. 实现处理逻辑

```python
async def _handle_file_upload(self, data: dict):
    """处理文件上传"""
    file_path = data.get("file_path")
    # 实现文件上传逻辑
    pass
```

#### 3. 在 mars-sandbox 中添加 API 端点

在 `mars-sandbox/backend/app/routers/` 中添加新的路由：

```python
# mars-sandbox/backend/app/routers/files.py
@router.post("/api/files/upload")
async def upload_file(request: FileUploadRequest):
    # 转发到对应节点的 WebSocket 连接
    await websocket_router.send_to_node(
        request.node_id, 
        {"type": "file_upload", **request.dict()}
    )
    # 等待结果并返回
```

#### 4. 创建 Skill 脚本

在 `home-agent-skill/home-hub/scripts/upload_file.py` 中创建上传脚本，调用 mars-sandbox HTTP API。

#### 5. 更新 SKILL.md

---

## SKILL.md 编写规范

Hermes Agent Skill 采用 YAML frontmatter + Markdown 格式：

```yaml
---
name: skill-name
description: 简短描述
version: 1.0.0
author: author-name
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [tag1, tag2]
    category: category-name
    requires_toolsets: [terminal]
required_environment_variables:
  - name: ENV_VAR_NAME
    prompt: 提示信息
    help: 帮助文本
    required_for: 用途说明
---

# Skill 名称

## 何时使用
描述触发条件

## 快速参考
表格列出常用操作

## 操作流程
分步骤说明

## 注意事项
```

Skill 路径规范：

```
~/.hermes/skills/
└── smart-home/           # 分类目录
    └── home-hub/         # Skill 目录
        ├── SKILL.md      # Skill 定义
        └── scripts/      # 可执行脚本
```

---

## 测试

### 本地测试 Home Agent

```bash
# 启动 home-agent（前台模式）
cd orbit-mind
python3 home-agent/main.py -c config.yaml

# 在另一个终端发送测试命令（需要同步等待结果）
cd orbit-mind
python3 home-agent-skill/home-hub/scripts/send_command.py home-server-01 "echo test" --timeout 10
```

### 端到端测试

1. 启动 mars-sandbox 服务
2. 启动 home-agent（家庭服务器），等待 WebSocket 连接成功
3. 通过 Hermes 发送命令（或直接用 send_command.py）
4. send_command.py 会同步返回执行结果
5. 检查审计日志：`cat ~/orbit-mind/logs/commands-$(date +%Y-%m-%d).jsonl`

### 单元测试示例

```python
import pytest
from shared.message_protocol import CommandMessage, ResultMessage

def test_command_message_serialization():
    cmd = CommandMessage(command="ls -la", timeout=30)
    json_str = cmd.to_json()
    cmd2 = CommandMessage.from_json(json_str)
    assert cmd2.command == "ls -la"
    assert cmd2.timeout == 30
    assert cmd2.type == "command"

def test_result_message_exit_codes():
    result = ResultMessage(request_id="test", exit_code=0, stdout="ok")
    assert result.exit_code == 0
    assert result.type == "result"
```

---

## 贡献指南

### 代码风格

- 使用 4 空格缩进
- 函数和类添加 docstring
- 类型注解（typing 模块）
- 变量命名使用 snake_case

### 提交规范

```
feat: 添加文件上传功能
fix: 修复心跳消息过期清理逻辑
refactor: 重构 WebSocket 客户端错误处理
docs: 更新部署文档
test: 添加消息协议单元测试
```

### 分支策略

- `main`：稳定版本
- `develop`：开发分支
- `feature/*`：功能分支
- `hotfix/*`：紧急修复
