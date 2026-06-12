# Orbit Mind

家庭AI中枢系统 —— 通过 WebSocket 长连接架构，统一管控智能家居设备、家庭信息看板、远程命令执行和电子墨水屏显示。

## 架构

```
IM → Hermes AI → mars-sandbox (服务端 + Web后台) ↔ home-agent (客户端) → 设备
```

- **mars-sandbox**: WebSocket 服务端 + Web 管理后台，负责节点管理、命令转发、看板推送
- **home-agent**: 部署在家庭服务器上的 WebSocket 客户端，接收并执行命令
- **mars-cli**: 命令行工具，专为大模型调用设计
- **EPD Tool**: BLE 电子墨水屏控制工具

## 技术栈

- 后端: [Python](https://www.python.org/) / [FastAPI](https://fastapi.tiangolo.com/) / [SQLAlchemy](https://www.sqlalchemy.org/) / [SQLite](https://www.sqlite.org/)
- 前端: [React](https://react.dev/) / [TypeScript](https://www.typescriptlang.org/) / [Vite](https://vitejs.dev/) / [Ant Design](https://ant.design/)
- 通信: [WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket) 长连接（节点管理 + 看板实时推送）
- 部署: [systemd](https://systemd.io/) / [nginx](https://nginx.org/)
- CLI: [Typer](https://typer.tiangolo.com/)
- BLE: 电子墨水屏控制

## 功能

### 家庭看板 (Dashboard)

全屏展示页面，iPad 横屏优化，WebSocket 实时推送。

- 食谱安排（周末菜单 + AI 智能生成）
- 生活/旅游计划
- 家庭留言板（置顶、颜色标识、过期管理、确认状态）
- 宠物互动（旺财/咪咪，点击互动 + 追球游戏 + 语音叫声 + 自言自语）
- 蝴蝶飞舞动效
- 每日箴言展示
- AI 壁纸生成（支持 Bing / Pexels 随机壁纸）
- 屏保模式（长期驻留省电优化）
- 星星墙展示（实时同步）
- 语音播报（浏览器 TTS）
- 远程控制看板屏保模式切换
- 背景图双层淡入淡出预加载

### 留言板 (Board)

- 留言增删改（内容/作者/颜色/过期时间）
- ColorPicker 颜色选择（10色预设 + 任意色）
- 家庭成员颜色自动关联
- 留言确认功能与家庭成员确认状态显示

### 食谱管理 (Meals)

- 菜品管理与历史记录
- AI 智能菜品生成（基于家庭偏好）
- 拍照识别菜品
- 喜好动态积累
- 菜单更新广播通知

### 儿童学习计划 (Schedule)

- 活动类型管理（自定义增删改）
- 周模板与每日计划排程
- 儿童学习星星奖励系统（奖励 / 兑换 / 汇总统计）
- 星星墙可视化展示

### 云盘 (Cloud Drive)

- 文件浏览/上传/下载
- 目录创建/复制/移动
- 签名 URL + 上传进度展示

### 视频管理 (Videos)

- 视频列表与在线播放
- 上传与处理（失败自动重试）

### 家庭设置 (Settings)

- 成员管理（添加/编辑/删除 + 头像长按编辑）
- 留言板默认颜色
- 节点管理与远程命令执行

## 快速开始

### 克隆仓库

```bash
git clone https://github.com/your-username/orbit-mind.git
cd orbit-mind
```

### 启动后端

```bash
cd mars-sandbox/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8888
```

### 启动前端

```bash
cd mars-sandbox/frontend
pnpm install
pnpm dev
```

访问 http://localhost:5173

### 部署 Home Agent

```bash
cd home-agent
pip install -r requirements.txt

# 配置
cp ../config.example.yaml ../config.yaml

# 设置环境变量
export MARS_SANDBOX_URL="ws://your-mars-sandbox-host:8888"
export HOME_AGENT_NODE_SECRET="your-node-secret"

# 运行
python main.py
```

配置优先级: 环境变量 > YAML 配置文件 > 默认值，详见 [config.example.yaml](config.example.yaml)。

### 安装 EPD Tool

```bash
cd tools/epd_tool
pip install -e .
epd-tool --help
```

## 项目结构

```
orbit-mind/
├── mars-sandbox/               # Web 管理后台
│   ├── backend/                #   FastAPI 后端
│   │   ├── app/routers/        #     API 路由（看板/留言/食谱/计划/星星/云盘/视频/节点/页面）
│   │   ├── app/services/       #     业务服务（AI、视频处理）
│   │   ├── app/ws/             #     WebSocket 模块（看板实时推送）
│   │   ├── app/utils/          #     公共工具函数
│   │   └── tests/              #     测试
│   ├── frontend/               #   React + Vite 前端
│   └── deploy.sh               #   部署脚本
├── home-agent/                 # 家庭服务器守护进程
├── shared/                     # 共享消息协议
├── tools/
│   ├── epd_tool/               # 电子墨水屏控制
│   └── mars-cli/               # CLI 工具
├── config.example.yaml         # 配置示例
└── LICENSE                     # Apache 2.0
```

## 安全

- 命令黑白名单
- 执行超时控制
- 审计日志
- 危险命令拦截
- WebSocket 连接认证（node_secret）

## License

Apache 2.0 - 详见 [LICENSE](LICENSE)。
