# WebSocket 迁移总结

## 迁移概述

本次迁移将 orbit-mind 项目从 MNS 消息中间件架构全面迁移到 WebSocket 长连接架构,彻底去除了对阿里云 MNS 的依赖。

## 架构变化

### 旧架构 (MNS)
```
IM → Hermes → MNS队列 ↔ Home-Agent → 设备
```

### 新架构 (WebSocket)
```
IM → Hermes → mars-sandbox (WebSocket服务端) ↔ home-agent (WebSocket客户端) → 设备
                    ↑
              HTTP API (节点管理/查询)
```

## 已完成的工作

### 1. 消息协议扩展 (shared/message_protocol.py)
新增消息类型:
- `RegisterMessage`: 节点注册消息
- `RegisterAckMessage`: 注册确认消息
- `HeartbeatMessage`: 心跳消息
- `HeartbeatAckMessage`: 心跳确认消息
- `ErrorMessage`: 错误消息

更新消息类型:
- `CommandMessage`: 增加 `source` 字段
- `ResultMessage`: `created_at` 改为 `timestamp`

### 2. 配置模块更新 (home-agent/config.py)
新增配置项:
- `mars_sandbox_url`: WebSocket 服务端地址
- `node_secret`: 节点密钥(用于连接认证)
- `heartbeat_interval`: 心跳间隔(秒)
- `reconnect_delay`: 重连延迟(秒)
- `max_reconnect_attempts`: 最大重连次数

移除配置项:
- 所有 MNS 相关配置(endpoint, access_key, queue_name等)

### 3. WebSocket 客户端实现 (home-agent/ws_client.py)
核心功能:
- WebSocket 连接管理
- 节点注册流程
- 心跳保活机制
- 命令接收和处理
- 结果发送
- 自动重连(指数退避)
- 连接异常处理

### 4. 主程序重构 (home-agent/main.py)
变更:
- 从同步模式改为异步模式(asyncio)
- 集成 WebSocket 客户端
- 移除 MNS 轮询逻辑
- 保持命令执行、安全校验、审计日志不变

### 5. Hermes Skill 脚本更新
**send_command.py**:
- 从发送到 MNS 队列改为调用 mars-sandbox HTTP API
- 从异步轮询改为同步等待结果
- 新增 node_id 参数指定目标节点
- 格式化输出执行结果

**poll_result.py**:
- 已删除(WebSocket 架构无需轮询)

### 6. 依赖更新 (home-agent/requirements.txt)
移除:
- `aliyun-mns-sdk`

新增:
- `websockets>=12.0`
- `aiohttp>=3.9.0`

### 7. 文档更新
- **SKILL.md**: 更新为 WebSocket 架构说明
- **README.md**: 更新架构图和使用说明
- **config.example.yaml**: 更新配置示例

### 8. 删除的文件
- `home-agent/mns_client.py`
- `home-agent/heartbeat.py`
- `home-agent-skill/home-hub/scripts/poll_result.py`

## 使用方式变化

### 旧方式 (MNS)
```bash
# 发送命令
python send_command.py "ls -la" --timeout 30
# 输出: REQUEST_ID=xxx

# 轮询结果
python poll_result.py <REQUEST_ID> --max-wait 60
```

### 新方式 (WebSocket)
```bash
# 发送命令并等待结果(同步)
python send_command.py <node_id> "ls -la" --timeout 30
# 直接输出执行结果
```

## 环境变量变化

### 移除的环境变量
- `MNS_ENDPOINT`
- `ALIBABA_CLOUD_ACCESS_KEY_ID`
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
- `MNS_QUEUE_NAME`

### 新增的环境变量
- `MARS_SANDBOX_URL`: mars-sandbox 服务地址
- `HOME_AGENT_NODE_SECRET`: 节点密钥

### 保留的环境变量
- `MARS_SANDBOX_API_KEY`: API 认证密钥
- `HOME_AGENT_NODE_ID`: 节点标识

## 优势对比

| 特性 | MNS 架构 | WebSocket 架构 |
|------|----------|----------------|
| 延迟 | 秒级(轮询) | 毫秒级(长连接) |
| 可靠性 | 依赖云服务 | 自动重连+心跳 |
| 成本 | MNS 按量计费 | 无额外成本 |
| 运维 | 需管理队列 | 集中管理 |
| 实时性 | 低 | 高 |
| 节点状态 | 难以感知 | 实时感知 |

## 后续工作

### mars-sandbox 端需要实现:
1. WebSocket 服务端(`/ws/agent/{node_id}`)
2. 连接认证中间件(验证 node_id 和 secret)
3. 连接池管理(Map<node_id, WebSocket>)
4. 消息分发器(根据 type 路由)
5. 心跳超时检测(180秒未收到心跳标记离线)
6. HTTP API(`/api/commands`)接收 Hermes 命令
7. 命令转发和结果返回逻辑

### 测试计划:
1. 单元测试: 消息序列化/反序列化、认证逻辑
2. 集成测试: 完整命令执行流程、断线重连
3. 压力测试: 多节点并发、长时间稳定性

## 回滚方案

如需回滚到 MNS 架构:
1. 恢复删除的文件(从 Git 历史)
2. 还原 requirements.txt
3. 还原 config.py 和 config.example.yaml
4. 还原 main.py 和 send_command.py

## 迁移完成标志

✅ 所有代码文件已更新
✅ 依赖已更新
✅ 文档已更新
✅ MNS 相关代码已删除
✅ WebSocket 客户端已实现
✅ 配置模块已更新
✅ 消息协议已扩展

---

**迁移日期**: 2024
**版本**: 2.0.0 (WebSocket)
