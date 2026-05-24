# 消息协议规范

本文档定义了家庭 AI 中枢系统中 WebSocket 传输的所有消息类型及其 JSON 格式。

## 通用规范

- **编码**：UTF-8 JSON 字符串（不使用 Base64 编码）
- **时间格式**：ISO 8601（UTC），示例：`2026-05-24T10:30:00.123456+00:00`
- **消息标识**：所有需要请求-响应配对的消息包含 `request_id`（UUID v4）
- **类型字段**：每条消息必须包含 `type` 字段用于消息路由

## 消息类型概览

| type | 方向 | 说明 |
|------|------|------|
| `register` | Home Agent → mars-sandbox | 节点注册请求 |
| `register_ack` | mars-sandbox → Home Agent | 注册确认响应 |
| `heartbeat` | Home Agent → mars-sandbox | 心跳消息 |
| `heartbeat_ack` | mars-sandbox → Home Agent | 心跳确认响应 |
| `command` | Hermes → Home Agent (via mars-sandbox) | 命令请求 |
| `result` | Home Agent → Hermes (via mars-sandbox) | 执行结果 |
| `error` | mars-sandbox ↔ Home Agent | 错误消息 |

---

## RegisterMessage

节点注册消息，由 Home Agent 在建立 WebSocket 连接后发送，用于向 mars-sandbox 注册节点信息。

### JSON 格式

```json
{
  "type": "register",
  "node_id": "home-server-01",
  "hostname": "home-server",
  "ip": "192.168.31.127",
  "platform": "Linux 5.15.0",
  "version": "1.0.0",
  "timestamp": "2026-05-24T10:30:00.123456+00:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 消息类型标识，固定为 `"register"` |
| `node_id` | string | 是 | 节点唯一标识 |
| `hostname` | string | 是 | 主机名 |
| `ip` | string | 是 | 局域网 IP 地址 |
| `platform` | string | 是 | 操作系统平台信息 |
| `version` | string | 是 | Home Agent 版本 |
| `timestamp` | string | 是 | 注册时间（ISO 8601 UTC） |

---

## RegisterAckMessage

注册确认消息，由 mars-sandbox 在收到注册请求后返回。

### JSON 格式

```json
{
  "type": "register_ack",
  "status": "success",
  "message": "节点注册成功",
  "timestamp": "2026-05-24T10:30:00.234567+00:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 消息类型标识，固定为 `"register_ack"` |
| `status` | string | 是 | 注册状态：`success` 或 `error` |
| `message` | string | 是 | 状态描述信息 |
| `timestamp` | string | 是 | 响应时间（ISO 8601 UTC） |

---

## HeartbeatMessage

心跳消息，由 Home Agent 定期发送到 mars-sandbox，用于维持连接和报告节点状态。

### JSON 格式

```json
{
  "type": "heartbeat",
  "node_id": "home-server-01",
  "uptime_seconds": 3600,
  "timestamp": "2026-05-24T11:30:00.123456+00:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 消息类型标识，固定为 `"heartbeat"` |
| `node_id` | string | 是 | 节点唯一标识 |
| `uptime_seconds` | int | 是 | 节点运行时长（秒） |
| `timestamp` | string | 是 | 心跳时间（ISO 8601 UTC） |

---

## HeartbeatAckMessage

心跳确认消息，由 mars-sandbox 在收到心跳后返回。

### JSON 格式

```json
{
  "type": "heartbeat_ack",
  "status": "ok",
  "timestamp": "2026-05-24T11:30:00.234567+00:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 消息类型标识，固定为 `"heartbeat_ack"` |
| `status` | string | 是 | 心跳状态，通常为 `"ok"` |
| `timestamp` | string | 是 | 响应时间（ISO 8601 UTC） |

---

## ErrorMessage

错误消息，用于在 mars-sandbox 和 Home Agent 之间传递错误信息。

### JSON 格式

```json
{
  "type": "error",
  "error_code": "AUTH_FAILED",
  "message": "节点密钥验证失败",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2026-05-24T10:30:00.123456+00:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 消息类型标识，固定为 `"error"` |
| `error_code` | string | 是 | 错误码 |
| `message` | string | 是 | 错误描述 |
| `request_id` | string | 否 | 关联的请求 ID（如果适用） |
| `timestamp` | string | 是 | 错误发生时间（ISO 8601 UTC） |

---

## CommandMessage

命令请求消息，由 Hermes Agent 通过 mars-sandbox WebSocket 发送到 Home Agent。

### JSON 格式

```json
{
  "type": "command",
  "command": "ls -la /home",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timeout": 30,
  "source": "hermes",
  "created_at": "2026-05-24T10:30:00.123456+00:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | string | 是 | `"command"` | 消息类型标识 |
| `command` | string | 是 | - | Shell 命令字符串 |
| `request_id` | string | 是 | - | 请求唯一标识（UUID v4） |
| `timeout` | int | 否 | `30` | 命令执行超时（秒），受 `max_timeout` 上限约束 |
| `source` | string | 否 | `"hermes"` | 命令来源 |
| `created_at` | string | 否 | 自动生成 | 消息创建时间（ISO 8601 UTC） |

### 约束

- `command` 不能为空字符串
- `timeout` 会被 Home Agent 的 `max_timeout` 配置限制（默认上限 120 秒）
- `command` 需通过安全校验（黑白名单）才能被执行

---

## ResultMessage

执行结果消息，由 Home Agent 在命令执行完成后通过 WebSocket 发送到 mars-sandbox，由 Hermes Agent 接收。

### JSON 格式

```json
{
  "type": "result",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "exit_code": 0,
  "stdout": "total 24\ndrwxr-xr-x  3 syb  syb  4096 May 20 10:00 .\n",
  "stderr": "",
  "duration_ms": 42,
  "timestamp": "2026-05-24T10:30:01.234567+00:00"
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
| `timestamp` | string | 是 | 自动生成 | 结果创建时间（ISO 8601 UTC） |

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

### mars-sandbox WebSocket 路由

```python
# mars-sandbox 服务端接收消息并路由
if msg_type == "register":
    # 处理节点注册
    await handle_register(websocket, data)
elif msg_type == "heartbeat":
    # 处理心跳
    await handle_heartbeat(websocket, data)
elif msg_type == "result":
    # 转发结果给 Hermes
    await forward_to_hermes(data)
else:
    # 转发命令到对应节点
    await forward_to_node(node_id, data)
```

### Home Agent 路由

```python
# Home Agent WebSocket 客户端接收消息
if msg_type == "command":
    # 执行命令
    result = await execute_command(cmd_msg)
    # 发送结果
    await ws_client.send_result(result)
elif msg_type == "heartbeat_ack":
    # 心跳确认，无需处理
    pass
elif msg_type == "error":
    # 记录错误
    logger.error(f"收到错误: {error.message}")
```

### Hermes Skill 路由

**send_command.py**：调用 mars-sandbox HTTP API 发送命令并同步等待结果

```python
# 调用 mars-sandbox API 发送命令
resp = requests.post(
    f"{base_url}/api/commands",
    json={"node_id": node_id, "command": command, "timeout": timeout},
    headers={"X-API-Key": api_key}
)
# 同步等待并返回结果
```

**list_nodes.py**：
```python
# 调用 mars-sandbox HTTP API
resp = requests.get(f"{base_url}/api/nodes", headers={"X-API-Key": api_key})
# 返回节点列表 JSON
```

---

## 协议版本

| 版本 | 变更说明 |
|------|----------|
| 2.0.0 | WebSocket 架构，支持 register/heartbeat/command/result/error 消息类型 |
| 1.1.0 | 移除 HeartbeatMessage，节点发现迁移到 mars-sandbox HTTP API (MNS 架构) |
| 1.0.0 | 初始版本，支持 command / result / heartbeat 三类消息 (MNS 架构) |

## 兼容性说明

- 消息解析采用宽松策略，未知字段会被忽略
- `type` 字段是唯一的路由标识，必须存在
- 缺少必要字段的消息会被记录错误日志后删除，不会导致系统崩溃
