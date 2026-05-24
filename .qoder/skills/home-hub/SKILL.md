---
name: home-hub
description: >-
  远程控制家庭 Linux 服务器。通过 mars-cli 在 home-agent 节点上执行 shell 命令、
  查询节点状态、管理服务。当用户需要在家庭服务器上执行命令、查看服务器状态、
  管理服务（docker/systemd）、排查问题时使用此 skill。
  触发词：家庭服务器、home server、远程命令、家里执行、家里的机器、节点状态
---

# Home Hub - 家庭服务器远程控制

通过 `mars-cli` 命令行工具与 mars-sandbox 中枢通信，在远程 home-agent 节点上执行 shell 命令并获取结果。

## 前提条件

`mars-cli` 必须已安装且配置完成。验证方法：

```bash
mars-cli health
mars-cli nodes
```

如果命令不可用或报错，参见项目根目录 `home-agent-skill/home-hub/README.md` 完成安装配置。

## 工作流程

### 1. 确认节点在线

在执行命令前，先查询在线节点：

```bash
mars-cli nodes
```

输出 JSON 中 `status: "online"` 的节点可用。记住 `node_id` 字段。

### 2. 执行远程命令

```bash
mars-cli exec <node_id> '<shell_command>' [--timeout <seconds>]
```

输出为 JSON，关键字段：
- `exit_code` — 0 表示成功，非 0 失败
- `stdout` — 标准输出
- `stderr` — 标准错误
- `duration_ms` — 执行耗时（毫秒）

CLI 退出码与远程命令 exit_code 一致。

### 3. 向用户反馈

将 stdout 内容整理返回。若 exit_code != 0，结合 stderr 说明失败原因。

## 命令速查

| 操作 | 命令 |
|------|------|
| 查看节点列表 | `mars-cli nodes` |
| 节点表格（人类可读） | `mars-cli nodes --table` |
| 执行远程命令 | `mars-cli exec <node_id> '<cmd>'` |
| 长耗时命令 | `mars-cli exec <node_id> '<cmd>' -t 120` |
| 服务健康检查 | `mars-cli health` |

## 常见用例

### 查看服务器状态
```bash
mars-cli exec home-server-01 'uname -a && df -h && free -h'
```

### 管理 systemd 服务
```bash
mars-cli exec home-server-01 'systemctl status docker'
mars-cli exec home-server-01 'systemctl restart nginx'
```

### Docker 操作
```bash
mars-cli exec home-server-01 'docker ps'
mars-cli exec home-server-01 'docker pull nginx:latest' -t 120
mars-cli exec home-server-01 'docker logs --tail 50 myapp'
```

### 系统排查
```bash
mars-cli exec home-server-01 'journalctl -u home-agent --no-pager -n 30'
mars-cli exec home-server-01 'ip addr show | grep inet'
mars-cli exec home-server-01 'cat /var/log/syslog | tail -20'
```

## 架构

```
Qoder → mars-cli (HTTP) → mars-sandbox → WebSocket → home-agent → 执行命令
                                                    ↓
                                              返回 JSON 结果
```

## 错误处理

| 错误 | 原因 | 处理 |
|------|------|------|
| 节点离线或不存在 | node_id 错误或节点断连 | 先 `mars-cli nodes` 确认在线 |
| 认证失败 | API Key 无效 | 检查环境变量或配置文件 |
| 命令执行超时 | 命令耗时超过 timeout | 增大 `-t` 参数 |
| 命令被安全策略拦截 | 命中危险命令黑名单 | 拆分命令或联系管理员 |
| 连接失败 | mars-sandbox 服务不可达 | `mars-cli health` 检查服务 |

## 注意事项

- 命令建议用**单引号**包裹，防止本地 shell 提前展开变量
- 默认超时 30 秒，安装软件/拉镜像等长操作需显式增大 `-t`
- 节点有安全策略（命令黑白名单），部分危险命令会被拒绝
- 所有命令执行都有审计日志记录
