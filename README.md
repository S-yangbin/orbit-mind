# Orbit Mind - 家庭AI中枢系统

Orbit Mind 是一个家庭AI中枢系统，包含多个组件用于实现智能家居控制、远程命令执行和电子墨水屏显示等功能。

## 项目结构

```
orbit-mind/
├── home-agent/              # 家庭服务器守护进程
│   ├── main.py             # 主程序入口
│   ├── config.py           # 配置管理模块
│   ├── mns_client.py       # 阿里云MNS客户端
│   ├── command_executor.py # 命令执行器
│   ├── security.py         # 安全校验模块
│   ├── command_logger.py   # 审计日志模块
│   └── requirements.txt    # Python依赖
├── home-agent-skill/        # Home Agent技能定义
│   └── home-hub/           # 家庭中枢技能
├── shared/                  # 共享模块
│   └── message_protocol.py # 消息协议定义
├── tools/                   # 工具集
│   └── epd_tool/           # 电子墨水屏控制工具
├── config.example.yaml      # 配置示例文件
└── LICENSE                  # Apache 2.0 许可证
```

## 主要组件

### 1. Home Agent (家庭服务器守护进程)

Home Agent 是一个长驻进程，通过阿里云消息服务(MNS)接收命令并执行，支持：

- **远程命令执行**: 通过MNS队列接收命令并执行
- **安全控制**: 支持黑白名单机制，防止危险命令执行
- **审计日志**: 记录所有命令执行情况
- **优雅退出**: 支持信号处理，安全关闭
- **systemd集成**: 提供systemd服务文件，便于部署

#### 快速开始

1. 安装依赖:
   ```bash
   cd home-agent
   pip install -r requirements.txt
   ```

2. 配置:
   ```bash
   cp ../config.example.yaml ../config.yaml
   # 编辑 config.yaml 填入MNS配置
   ```

3. 运行:
   ```bash
   python main.py
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

项目使用标准化的JSON消息格式进行通信：

- **CommandMessage**: 命令消息，包含要执行的命令和超时设置
- **ResultMessage**: 结果消息，包含命令执行结果和退出码

## 配置说明

项目支持多种配置方式，优先级从高到低：

1. 环境变量
2. YAML配置文件
3. 默认值

详见 [config.example.yaml](config.example.yaml) 获取配置示例。

## 安全特性

- 命令黑白名单机制
- 命令执行超时控制
- 审计日志记录
- 危险命令拦截

## 许可证

本项目采用 Apache 2.0 许可证，详见 [LICENSE](LICENSE) 文件。