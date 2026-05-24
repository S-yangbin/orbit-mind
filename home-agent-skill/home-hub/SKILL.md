---
name: home-hub
description: 远程控制家庭 Linux 服务器，通过阿里云 MNS 消息队列发送命令并获取执行结果
version: 1.0.0
author: syb
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [automation, remote-control, home-server, mns]
    category: smart-home
    requires_toolsets: [terminal]
required_environment_variables:
  - name: ALIBABA_CLOUD_ACCESS_KEY_ID
    prompt: 阿里云 AccessKey ID
    help: 在阿里云控制台获取 AccessKey
    required_for: MNS 消息队列认证
  - name: ALIBABA_CLOUD_ACCESS_KEY_SECRET
    prompt: 阿里云 AccessKey Secret
    help: 在阿里云控制台获取 AccessKey
    required_for: MNS 消息队列认证
  - name: MNS_ENDPOINT
    prompt: MNS 服务端点（如 https://xxx.mns.cn-qingdao.aliyuncs.com）
    help: 在阿里云轻量消息队列控制台获取
    required_for: 连接 MNS 服务
  - name: MNS_QUEUE_NAME
    prompt: MNS 队列名称
    help: 在阿里云轻量消息队列控制台查看
    required_for: 指定消息队列
---

# Home Hub - 家庭服务器远程控制

通过阿里云轻量消息队列（MNS）向家庭 Linux 服务器发送命令并获取执行结果。

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
| 发送命令 | `python scripts/send_command.py "your_command" --timeout 30` |
| 轮询结果 | `python scripts/poll_result.py <request_id> --max-wait 60` |

## 操作流程

### 步骤 1：发送命令

使用终端执行 send_command.py 脚本，将命令发送到 MNS 队列：

```bash
cd ~/.hermes/skills/smart-home/home-hub
python scripts/send_command.py "ls -la /home" --timeout 30
```

脚本会输出一个 `request_id`（UUID），例如：
```
REQUEST_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### 步骤 2：轮询结果

使用步骤 1 返回的 request_id 轮询执行结果：

```bash
cd ~/.hermes/skills/smart-home/home-hub
python scripts/poll_result.py "a1b2c3d4-e5f6-7890-abcd-ef1234567890" --max-wait 60
```

脚本会输出命令的执行结果（JSON 格式），包含：
- `exit_code`: 退出码（0 表示成功）
- `stdout`: 标准输出
- `stderr`: 标准错误
- `duration_ms`: 执行耗时

### 步骤 3：向用户反馈

将执行结果整理后返回给用户。如果命令执行失败（exit_code != 0），告知用户错误原因。

## 常见用例

### 查看服务器状态
```bash
python scripts/send_command.py "uname -a && df -h && free -h" --timeout 15
```

### 管理服务
```bash
python scripts/send_command.py "systemctl status docker" --timeout 10
python scripts/send_command.py "systemctl restart nginx" --timeout 30
```

### 执行长时间任务（增加超时）
```bash
python scripts/send_command.py "docker pull nginx:latest" --timeout 120
```

## 注意事项

- 命令在家庭服务器上以配置的工作目录执行
- 命令执行有超时保护（默认 30 秒，最大 120 秒）
- 危险命令（如 `rm -rf /`）会被安全策略拦截
- 输出内容过长时会被自动截断
- 轮询结果时如果超过 max-wait 秒仍未收到结果，会返回超时提示
- 如果命令执行时间较长（如编译、下载），建议设置较大的 timeout 和 max-wait

## 验证

执行以下命令验证 Skill 是否正常工作：

```bash
cd ~/.hermes/skills/smart-home/home-hub
python scripts/send_command.py "echo 'hello from home server'" --timeout 10
```

如果成功输出 request_id，说明发送正常。然后用该 request_id 轮询结果，如果收到 `hello from home server`，说明整个链路通畅。
