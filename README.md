# Orbit Mind - 家庭AI中枢系统 (WebSocket 架构)

Orbit Mind 是一个家庭AI中枢系统,采用 WebSocket 长连接架构,实现智能家居控制、远程命令执行和电子墨水屏显示等功能。

## 架构概览

```
IM → Hermes → mars-sandbox (WebSocket服务端) ↔ home-agent (WebSocket客户端) → 设备
                    ↑
              HTTP API (节点管理/查询)
```

### 核心组件

- **mars-sandbox**: WebSocket服务端,负责节点管理、命令转发和结果返回
- **home-agent**: WebSocket客户端,连接到mars-sandbox,接收并执行命令
- **Hermes**: AI代理,通过HTTP API调用mars-sandbox发送命令
- **EPD Tool**: 电子墨水屏控制工具,通过BLE控制显示设备

## 项目结构

```
orbit-mind/
├── home-agent/              # 家庭服务器守护进程 (WebSocket客户端)
│   ├── main.py             # 主程序入口
│   ├── config.py           # 配置管理模块
│   ├── ws_client.py        # WebSocket客户端
│   ├── command_executor.py # 命令执行器
│   ├── security.py         # 安全校验模块
│   ├── command_logger.py   # 审计日志模块
│   └── requirements.txt    # Python依赖
├── home-agent-skill/        # Hermes技能定义
│   └── home-hub/           # 家庭中枢技能
├── shared/                  # 共享模块
│   └── message_protocol.py # WebSocket消息协议定义
├── tools/                   # 工具集
│   └── epd_tool/           # 电子墨水屏控制工具
├── config.example.yaml      # 配置示例文件
└── LICENSE                  # Apache 2.0 许可证
```

## 主要组件

### 1. Home Agent (家庭服务器守护进程)

Home Agent 是一个长驻进程,通过 WebSocket 连接 mars-sandbox 接收命令并执行,支持:

- **实时命令执行**: WebSocket长连接,毫秒级延迟
- **自动重连**: 指数退避重连机制,保证连接可靠性
- **心跳保活**: 定期发送心跳,实时感知节点状态
- **安全控制**: 支持黑白名单机制,防止危险命令执行
- **审计日志**: 记录所有命令执行情况
- **优雅退出**: 支持信号处理,安全关闭
- **systemd集成**: 提供systemd服务文件,便于部署

#### 快速开始

1. 安装依赖:
   ```bash
   cd home-agent
   pip install -r requirements.txt
   ```

2. 配置:
   ```bash
   cp ../config.example.yaml ../config.yaml
   # 编辑 config.yaml 填入mars-sandbox配置
   ```

3. 运行:
   ```bash
   python main.py
   ```

4. 设置环境变量:
   ```bash
   export MARS_SANDBOX_URL="ws://your-mars-sandbox-host:8888"
   export HOME_AGENT_NODE_SECRET="your-node-secret"
   ```

### 2. EPD Tool (电子墨水屏控制工具)

EPD Tool 是一个通过BLE控制电子墨水屏设备的命令行工具，支持多种尺寸的电子墨水屏。

#### 功能特性

- 支持多种尺寸的电子墨水屏(4.2寸、5.83寸、7.5寸等)
- 支持黑白、三色、四色显示
- 图像显示和文字渲染
- 设备配置和管理
- BLE连接控制

#### 安装使用

```bash
cd tools/epd_tool
pip install -e .
epd-tool --help
```

### 3. 消息协议

项目使用WebSocket进行实时通信,消息格式为JSON:

- **RegisterMessage**: 节点注册消息
- **HeartbeatMessage**: 心跳消息
- **CommandMessage**: 命令消息,包含要执行的命令和超时设置
- **ResultMessage**: 结果消息,包含命令执行结果和退出码
- **ErrorMessage**: 错误消息

## 配置说明

项目支持多种配置方式,优先级从高到低:

1. 环境变量
2. YAML配置文件
3. 默认值

详见 [config.example.yaml](config.example.yaml) 获取配置示例。

### 关键配置项

- `mars_sandbox_url`: mars-sandbox WebSocket地址
- `node_secret`: 节点密钥(用于WebSocket连接认证)
- `heartbeat_interval`: 心跳间隔(秒)
- `reconnect_delay`: 重连延迟(秒)

## 安全特性

- 命令黑白名单机制
- 命令执行超时控制
- 审计日志记录
- 危险命令拦截
- WebSocket连接认证(node_secret)

## 架构优势

- **低延迟**: WebSocket长连接,毫秒级响应
- **高可靠**: 自动重连+心跳检测,实时感知节点状态
- **易运维**: 集中管理,无需维护消息队列
- **低成本**: 去除云服务依赖,减少外部依赖
- **易扩展**: 支持多节点并发,支持实时交互场景

## 许可证

本项目采用 Apache 2.0 许可证，详见 [LICENSE](LICENSE) 文件。