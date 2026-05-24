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

定义三种消息类型的数据类，均支持 JSON 序列化/反序列化。

```python
from shared.message_protocol import (
    CommandMessage,     # 命令消息
    ResultMessage,      # 结果消息
    HeartbeatMessage,   # 心跳消息
    parse_message,      # 解析 JSON → dict
    is_command_message, # 类型判断
    is_result_message,
    is_heartbeat_message,
)

# 创建命令消息
cmd = CommandMessage(command="ls -la", timeout=30)
json_str = cmd.to_json()

# 从 JSON 恢复
cmd2 = CommandMessage.from_json(json_str)

# 类型判断
data = parse_message(json_str)
if is_command_message(data):
    print("这是一条命令")
```

**扩展新消息类型**：

1. 在 `message_protocol.py` 添加新的 `@dataclass` 类
2. 添加对应的 `is_xxx_message()` 判断函数
3. 在 `main.py` 的 `process_message()` 中添加路由分支

### mns_client.py（MNS 客户端）

位置：`home-agent/mns_client.py`

封装阿里云 MNS SDK，提供简洁的操作接口。

```python
from mns_client import MNSClient

client = MNSClient(
    endpoint="https://xxx.mns.cn-qingdao.aliyuncs.com",
    access_key_id="ak",
    access_key_secret="sk",
    queue_name="mate-notify",
)

# 发送消息
msg_id = client.send_message('{"type": "command", ...}')

# 长轮询接收（阻塞 wait_seconds 秒）
result = client.receive_message(wait_seconds=30)
if result:
    receipt_handle, message_body = result

# 删除消息
client.delete_message(receipt_handle)

# 窥视消息（不删除、不改变可见性）
msgs = client.peek_message(num=16)
for body, msg_id in msgs:
    print(body)

# Re-send + Delete（单队列核心操作）
client.resend_and_delete(receipt_handle, message_body)
```

**关键设计：`resend_and_delete`**

MNS 队列中只有一份消息，当 home-agent 收到不属于自己的消息（如 result）时，需要：
1. 先将消息重新发回队列（新 message_id）
2. 再删除自己消费的这份

这保证了消息不丢失，同时让消息重新进入队列等待正确的消费者。

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

### heartbeat.py（心跳发送器）

位置：`home-agent/heartbeat.py`

```python
from heartbeat import HeartbeatSender

# 通过 HTTP 上报到 mars-sandbox
sender = HeartbeatSender(
    base_url="http://8.213.135.161:8888",
    api_key="your-api-key",
    node_id="home-01",
    interval=60,
)
sender.start()   # 启动后台线程，立即发送一次，之后每 60s 发送
sender.stop()    # 停止（等待线程退出）
sender.send_once()  # 手动触发一次
```

---

## 添加新功能

### 示例：添加文件上传功能

#### 1. 定义新消息类型

在 `shared/message_protocol.py` 中：

```python
@dataclass
class FileUploadMessage:
    file_path: str
    request_id: str = None
    type: str = "file_upload"
    chunk_size: int = 65536
    created_at: str = None
    
    # ... 与其他消息类型相同的 to_json/from_dict 方法

def is_file_upload_message(data: dict) -> bool:
    return data.get("type") == "file_upload"
```

#### 2. 添加处理逻辑

在 `home-agent/main.py` 中：

```python
from shared.message_protocol import is_file_upload_message

def process_message(mns_client, receipt_handle, message_body, config, audit_logger):
    data = parse_message(message_body)
    
    if is_command_message(data):
        _handle_command(...)
    elif is_result_message(data):
        _handle_result_passthrough(...)
    elif is_heartbeat_message(data):
        _handle_heartbeat(...)
    elif is_file_upload_message(data):  # 新增
        _handle_file_upload(...)        # 新增
    else:
        delete_message(...)
```

#### 3. 创建 Skill 脚本

在 `home-agent-skill/home-hub/scripts/upload_file.py` 中创建上传脚本。

#### 4. 更新 SKILL.md

在 SKILL.md 中添加文件上传的使用说明。

### 示例：添加多节点广播命令

修改 `send_command.py` 支持指定目标节点：

```python
# 在消息中增加 target_node 字段
message = {
    "request_id": request_id,
    "type": "command",
    "command": args.command,
    "timeout": args.timeout,
    "target_node": args.node,  # 新增：目标节点 ID
    "created_at": datetime.now(timezone.utc).isoformat(),
}
```

在 `main.py` 中检查 `target_node` 是否匹配当前节点。

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

# 在另一个终端发送测试命令
cd orbit-mind
python3 home-agent-skill/home-hub/scripts/send_command.py "echo test" --timeout 10
```

### 端到端测试

1. 启动 home-agent（家庭服务器）
2. 通过 Hermes 发送命令（或直接用 send_command.py）
3. 用 poll_result.py 轮询结果
4. 检查审计日志：`cat ~/orbit-mind/logs/commands-$(date +%Y-%m-%d).jsonl`

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
refactor: 重构 MNS 客户端错误处理
docs: 更新部署文档
test: 添加消息协议单元测试
```

### 分支策略

- `main`：稳定版本
- `develop`：开发分支
- `feature/*`：功能分支
- `hotfix/*`：紧急修复
