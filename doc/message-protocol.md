# 消息协议规范

本文档定义了家庭 AI 中枢系统中 MNS 队列传输的所有消息类型及其 JSON 格式。

## 通用规范

- **编码**：UTF-8 JSON 字符串（不使用 Base64 编码）
- **时间格式**：ISO 8601（UTC），示例：`2026-05-24T10:30:00.123456+00:00`
- **消息标识**：所有需要请求-响应配对的消息包含 `request_id`（UUID v4）
- **类型字段**：每条消息必须包含 `type` 字段用于消息路由

## 消息类型概览

| type | 方向 | 说明 |
|------|------|------|
| `command` | Hermes → Home Agent | 命令请求 |
| `result` | Home Agent → Hermes | 执行结果 |

> **节点发现已迁移**：心跳消息不再通过 MNS 队列传输。节点心跳通过 HTTP API 上报到 mars-sandbox 服务进行持久化管理。详见 `doc/architecture.md`。

---

## CommandMessage

命令请求消息，由 Hermes Agent 的 `send_command.py` 发送到 MNS 队列，由 Home Agent 消费执行。

### JSON 格式

```json
{
  "type": "command",
  "command": "ls -la /home",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timeout": 30,
  "created_at": "2026-05-24T10:30:00.123456+00:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | string | 是 | `"command"` | 消息类型标识 |
| `command` | string | 是 | - | Shell 命令字符串 |
| `request_id` | string | 否 | 自动生成 UUID | 请求唯一标识 |
| `timeout` | int | 否 | `30` | 命令执行超时（秒），受 `max_timeout` 上限约束 |
| `created_at` | string | 否 | 自动生成 | 消息创建时间（ISO 8601 UTC） |

### 约束

- `command` 不能为空字符串
- `timeout` 会被 Home Agent 的 `max_timeout` 配置限制（默认上限 120 秒）
- `command` 需通过安全校验（黑白名单）才能被执行

---

## ResultMessage

执行结果消息，由 Home Agent 在命令执行完成后发送到 MNS 队列，由 Hermes Agent 的 `poll_result.py` 消费。

### JSON 格式

```json
{
  "type": "result",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "exit_code": 0,
  "stdout": "total 24\ndrwxr-xr-x  3 syb  syb  4096 May 20 10:00 .\n",
  "stderr": "",
  "duration_ms": 42,
  "created_at": "2026-05-24T10:30:01.234567+00:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | string | 是 | `"result"` | 消息类型标识 |
| `request_id` | string | 是 | - | 对应 CommandMessage 的 request_id |
| `exit_code` | int | 是 | - | 命令退出码 |
| `stdout` | string | 否 | `""` | 标准输出（截断至 64,000 字符） |
| `stderr` | string | 否 | `""` | 标准错误（截断至 16,000 字符） |
| `duration_ms` | int | 否 | `0` | 命令执行耗时（毫秒） |
| `created_at` | string | 否 | 自动生成 | 结果创建时间（ISO 8601 UTC） |

### 特殊 exit_code

| exit_code | 含义 |
|-----------|------|
| `0` | 命令执行成功 |
| `-1` | 命令执行超时 |
| `-2` | 命令执行异常（如进程启动失败） |
| `-100` | 命令被安全策略拦截（黑白名单） |
| `> 0` | 命令自身返回的非零退出码 |

### 输出截断规则

| 输出流 | 最大长度 | 截断策略 |
|--------|----------|----------|
| `stdout` | 64,000 字符 | 保留末尾内容（`[-64000:]`） |
| `stderr` | 16,000 字符 | 保留末尾内容（`[-16000:]`） |

---

## 消息路由规则

### Home Agent 路由

```python
if is_command_message(data):
    # 执行命令，发送 result，删除原消息
    _handle_command(...)
elif is_result_message(data):
    # re-send 回队列，删除原消息（result 是给 Hermes 的）
    _handle_result_passthrough(...)
else:
    # 未知类型，直接删除
    delete_message(...)
```

### Hermes Skill 路由

**send_command.py**：只发送，不消费

**poll_result.py**：
```python
if msg_type == "result" and msg_request_id == target_request_id:
    # 找到目标结果，删除并输出
    delete + print(result)
else:
    # 非目标消息，re-send 回队列后删除
    send + delete
```

**list_nodes.py**：
```python
# 调用 mars-sandbox HTTP API
resp = requests.get(f"{base_url}/api/nodes", headers={"X-API-Key": api_key})
# 返回节点列表 JSON
```

---

## 历史：HeartbeatMessage（已废弃）

> 心跳消息已迁移到 mars-sandbox HTTP API，不再通过 MNS 队列传输。
> `HeartbeatMessage` 和 `is_heartbeat_message()` 已从 `message_protocol.py` 中移除。

---

## 协议版本

| 版本 | 变更说明 |
|------|----------|
| 1.1.0 | 移除 HeartbeatMessage，节点发现迁移到 mars-sandbox HTTP API |
| 1.0.0 | 初始版本，支持 command / result / heartbeat 三类消息 |

## 兼容性说明

- 消息解析采用宽松策略，未知字段会被忽略
- `type` 字段是唯一的路由标识，必须存在
- 缺少必要字段的消息会被记录错误日志后删除，不会导致系统崩溃
