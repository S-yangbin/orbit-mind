---
name: mars-cli
description: >-
  mars-sandbox 家庭中枢管理平台 CLI 客户端。通过终端执行 mars-cli 命令，
  管理远程节点、留言板、餐饮计划、视频学习、云盘、页面、标签、看板壁纸、
  儿童学习计划、星星奖励等。
  看板壁纸支持从 Bing + Pexels 壁纸池（约23张）随机刷新。
  支持语音播报留言板、学习计划、今日菜谱等内容到 Dashboard。
  支持远程切换屏保模式、切换页面。
  支持星星奖励系统：颁发星星、查看汇总、兑换、撤回。
  当用户提到：家庭服务器、留言板、餐饮计划、菜单、视频学习、云盘文件、
  页面管理、节点管理、远程命令执行、刷新壁纸、换壁纸、看板、
  学习计划、作业、课程安排、今日计划、播报、朗读、语音播放、屏保、熄屏、
  星星、奖励、积分、兑换时触发。
  当用户说「让小皮帮我做xxx」或提到「小皮」相关请求时，也应触发本 Skill。
compatibility: Requires mars-cli installed on the server, and mars-sandbox service running.
metadata:
  author: orbit-mind
  version: "1.0"
  tags: [automation, remote-control, home-server, cli, meal-planning, drive, video-learning, schedule]
  category: smart-home
required_environment_variables:
  - name: MARS_SANDBOX_URL
    prompt: mars-sandbox 服务地址（如 http://<your-server-ip>:8888）
    help: mars-sandbox 服务的 HTTP API 地址
    required_for: 所有 mars-cli 命令
  - name: MARS_SANDBOX_API_KEY
    prompt: mars-sandbox API Key
    help: 在 mars-sandbox 管理后台获取
    required_for: nodes/pages/tags/scan 等 API Key 认证模块
  - name: MARS_SANDBOX_USERNAME
    prompt: mars-sandbox 登录用户名
    help: board/meals/videos/drive/schedule 等 Cookie 认证模块需要
    required_for: 留言板、餐饮计划、视频学习、云盘、学习计划模块
  - name: MARS_SANDBOX_PASSWORD
    prompt: mars-sandbox 登录密码
    help: board/meals/videos/drive/schedule 等 Cookie 认证模块需要
    required_for: 留言板、餐饮计划、视频学习、云盘、学习计划模块
---

# mars-cli — 家庭中枢管理平台 CLI

通过 `mars-cli` 命令行工具操作 mars-sandbox 全部功能模块。

## 何时使用

当用户需要：
- 在家庭服务器上执行远程命令
- 管理家庭留言板
- 查看或生成餐饮计划、管理菜品和用餐记录
- 管理视频学习（分段、笔记、进度）
- 管理云盘文件
- 管理页面和标签
- 查看节点状态
- 刷新看板壁纸
- 管理儿童学习计划（活动类型、周模板、每日计划、完成情况）
- 管理星星奖励（颁发、查看、兑换、撤回）
- 语音播报留言板、学习计划、今日菜谱等内容到 Dashboard
- 控制看板进入屏保模式或唤醒看板

触发关键词：家庭服务器、留言板、餐饮计划、菜单、吃什么、视频学习、云盘、页面管理、节点、远程命令、壁纸、看板、学习计划、作业、今日计划、播报、朗读、语音播放、TTS、屏保、熄屏、星星、奖励、积分、兑换

## 前提条件

### 检查 mars-cli 是否安装

```bash
mars-cli --help
```

如果未安装：
```bash
pip install mars-cli
```

### 检查配置

mars-cli 需要配置服务地址和认证信息（三选一，优先级从高到低）：
1. 命令行参数：`mars-cli --url http://... --api-key xxx <command>`
2. 环境变量：`MARS_SANDBOX_URL` / `MARS_SANDBOX_API_KEY` / `MARS_SANDBOX_USERNAME` / `MARS_SANDBOX_PASSWORD`
3. 配置文件：`mars-cli.json`（支持路径：`./mars-cli.json`、`~/.config/mars-cli/config.json`、`~/.mars-cli.json`）

配置文件格式：
```json
{
  "url": "http://localhost:8888",
  "api_key": "your-api-key",
  "username": "admin",
  "password": "your-password",
  "default_node": "home-server-01",
  "default_timeout": 30
}
```

验证连接：
```bash
mars-cli health
```

## 功能模块总览

| 模块 | 命令前缀 | 说明 | 认证方式 |
|------|----------|------|----------|
| 健康检查 | `mars-cli health` | 服务状态检查 | 无需认证 |
| 节点管理 | `mars-cli nodes` | 节点列表、远程命令执行 | API Key |
| 留言板 | `mars-cli board` | 家庭留言管理 | Cookie（自动登录） |
| 餐饮计划 | `mars-cli meals` | 成员、菜品、菜单、用餐记录 | Cookie（自动登录） |
| 视频学习 | `mars-cli videos` | 视频、分段、笔记、进度 | Cookie（自动登录） |
| 云盘 | `mars-cli drive` | 文件/文件夹管理 | Cookie（自动登录） |
| 页面管理 | `mars-cli pages` | 托管页面 CRUD | API Key |
| 标签管理 | `mars-cli tags` | 标签 CRUD | API Key |
| 扫描 | `mars-cli scan` | 页面目录扫描 | API Key |
| 看板 | `mars-cli dashboard` | 壁纸刷新等看板管理 | Cookie（自动登录）/ API Key |
| 学习计划 | `mars-cli schedule` | 活动类型、周模板、每日计划 | Cookie（自动登录） |
| 星星奖励 | `mars-cli stars` | 星星奖励与兑换 | Cookie（自动登录） |

## 命令参考

### 健康检查

```bash
mars-cli health
```

### 节点管理 (`nodes`)

```bash
mars-cli nodes list [--stale 180] [--table]
mars-cli nodes delete <node_id>
mars-cli nodes exec <node_id> '<command>' [-t 30]
```

| 命令 | 说明 |
|------|------|
| `nodes list` | 列出所有节点及在线状态 |
| `nodes delete <node_id>` | 删除节点注册记录 |
| `nodes exec <node_id> '<cmd>' -t <秒>` | 在远程节点执行 shell 命令 |

**exec 说明：** 命令通过 WebSocket 转发到目标节点的 home-agent 执行，危险命令会被安全策略拦截。CLI 退出码与远程命令 exit_code 一致。

### 留言板 (`board`)

```bash
mars-cli board list [--json/--no-json]
mars-cli board add '<content>' [-a '<author>'] [-c yellow|red|blue|green|pink] [-e YYYY-MM-DD]
mars-cli board update <message_id> [--content '...'] [--author '...'] [--color '...'] [--expires '...']
mars-cli board delete <message_id>
mars-cli board pin <message_id>
```

### 餐饮计划 (`meals`)

#### 家庭成员 (`meals members`)

```bash
mars-cli meals members list
mars-cli meals members add '<name>' [--avatar '🧑'] [--color '#hex']
mars-cli meals members update <member_id> [--name '...'] [--avatar '...']
mars-cli meals members delete <member_id>
```

#### 菜品库 (`meals dishes`)

```bash
mars-cli meals dishes list [-q '<keyword>'] [--category '<分类>'] [--page N] [--page-size N]
mars-cli meals dishes get <dish_id>
mars-cli meals dishes add '<name>' [-c '<分类>'] [--recipe '<做法>']
```

菜品分类：`荤菜`、`素菜`、`汤`、`主食` 等。

#### 菜单计划 (`meals plan`)

```bash
mars-cli meals plan current
mars-cli meals plan generate [--week-start YYYY-MM-DD]
mars-cli meals plan confirm
mars-cli meals plan add <YYYY-MM-DD> <breakfast|lunch|dinner> <dish_id>
mars-cli meals plan replace <item_id> <dish_id>
mars-cli meals plan remove <item_id>
```

**注意：** `plan generate` 使用 AI 生成月度菜单，耗时较长（可能需要 60-120 秒）。

#### 用餐记录 (`meals history`)

```bash
mars-cli meals history list [--page N] [--page-size N] [--start YYYY-MM-DD] [--end YYYY-MM-DD]
mars-cli meals history stats [--days 14]
mars-cli meals history add <YYYY-MM-DD> <breakfast|lunch|dinner> '<dishes_json>' [--image '...'] [--rating 1-5] [--note '...']
```

dishes JSON 格式：`'[{"name":"红烧肉"},{"dish_id":5,"name":"青菜"}]'`

#### 偏好 (`meals preferences`)

```bash
mars-cli meals preferences list
mars-cli meals preferences dish <dish_id>
```

### 视频学习 (`videos`)

```bash
mars-cli videos list [-q '<keyword>'] [--status '<status>'] [--page N] [--page-size N]
mars-cli videos get <video_id>
mars-cli videos process <video_id>
mars-cli videos segments add <video_id> '<title>' <start_sec> <end_sec> [--type qa|intro|practice] [--transcription '...']
mars-cli videos segments update <segment_id> [--title '...'] [--start N] [--end N]
mars-cli videos segments delete <segment_id>
mars-cli videos note <segment_id> '<markdown_content>'
mars-cli videos progress <segment_id> [--mastered 0|1] [--loops N]
```

### 云盘 (`drive`)

```bash
mars-cli drive list [-p <parent_id>] [-q '<keyword>'] [--page N] [--page-size N]
mars-cli drive folders
mars-cli drive mkdir '<name>' [-p <parent_id>]
mars-cli drive rm <file_id>
mars-cli drive rmdir <folder_id>
mars-cli drive move <file_id> [<target_parent_id>]
mars-cli drive copy <file_id> [<target_parent_id>]
mars-cli drive url '<oss_key>' [--expires 3600]
mars-cli drive preview '<oss_key>' [--page N] [--lines N]
```

### 页面管理 (`pages`)

```bash
mars-cli pages list [-q '<keyword>'] [--tag '<tag>'] [--category '<cat>'] [--page N] [--page-size N]
mars-cli pages get <page_id>
mars-cli pages update <page_id> [--title '...'] [--description '...'] [--category '...'] [--tags 'a,b,c']
mars-cli pages delete <page_id>
```

### 标签管理 (`tags`)

```bash
mars-cli tags list
mars-cli tags create '<name>'
mars-cli tags update <tag_id> '<new_name>'
mars-cli tags delete <tag_id>
```

### 扫描 (`scan`)

```bash
mars-cli scan trigger
mars-cli scan status
```

### 看板 (`dashboard`)

```bash
mars-cli dashboard refresh-wallpaper
mars-cli dashboard generate-wallpaper [--prompt '自定义描述']
mars-cli dashboard list-wallpapers
mars-cli dashboard set-wallpaper <filename>
mars-cli dashboard broadcast [--source messages|schedule|meals|text] [--text '...'] [--page 0|1]
mars-cli dashboard switch-page <0|1> [--auto-rotate] [--interval 30]
mars-cli dashboard screensaver <true|false>
```

| 命令 | 说明 |
|------|------|
| `dashboard refresh-wallpaper` | 从 Bing + Pexels 壁纸池（~23张）随机刷新看板壁纸，推送到所有已连接的 Dashboard |
| `dashboard generate-wallpaper` | AI 生成高清风景壁纸并推送到所有已连接的 Dashboard（耗时约 30-90 秒） |
| `dashboard list-wallpapers` | 列出所有已生成的 AI 壁纸，显示文件名、URL、大小、创建时间 |
| `dashboard set-wallpaper <filename>` | 设置指定壁纸并推送到所有已连接的 Dashboard |
| `dashboard broadcast --source messages` | 语音播报留言板内容（默认，最多 10 条） |
| `dashboard broadcast --source schedule` | 语音播报今日学习计划及完成情况 |
| `dashboard broadcast --source meals` | 语音播报今日菜谱（午餐/晚餐） |
| `dashboard broadcast --source text --text '...'` | 播报自定义文本 |
| `dashboard broadcast --page 0` | 播报时自动切换到家庭看板页 |
| `dashboard switch-page 0` | 远程切换到家庭看板页 |
| `dashboard switch-page 1` | 远程切换到学习计划页 |
| `dashboard switch-page 0 --auto-rotate --interval 60` | 启动自动轮播，每 60 秒切换一次 |
| `dashboard screensaver true` | 立即进入屏保模式（仅展示壁纸） |
| `dashboard screensaver false` | 唤醒看板（恢复内容展示） |

### 学习计划 (`schedule`)

#### 活动类型 (`schedule types`)

```bash
mars-cli schedule types list
mars-cli schedule types add '<name>' [--icon '📚'] [--color '#hex'] [--category '<cat>']
mars-cli schedule types update <type_id> [--name '...'] [--icon '...'] [--color '...']
mars-cli schedule types delete <type_id>
```

活动分类: `homework`（作业）、`reading`（绘本）、`sports`（运动）、`arts`（才艺）、`freeplay`（自由玩耆）、`custom`（自定义）。
预设类型（做作业📝、读绘本📖、运动🏀、才艺♟️、自由玩耆🎮）不可删除。

#### 周模板 (`schedule template`)

```bash
mars-cli schedule template get
mars-cli schedule template set '<template_json>'
```

template JSON 格式：
```json
{"name": "默认周计划", "days": {"mon": [1,3], "tue": [2,4], "wed": [1], "thu": [3,5], "fri": [1], "sat": [2,4,5], "sun": [5]}}
```

`days` 的 key 为 `mon/tue/wed/thu/fri/sat/sun`，value 为活动类型 ID 数组。

#### 每日计划

```bash
mars-cli schedule today
mars-cli schedule daily <YYYY-MM-DD>
mars-cli schedule add <YYYY-MM-DD> <activity_type_id>
mars-cli schedule complete <item_id> [--note '完成情况说明']
mars-cli schedule uncomplete <item_id>
mars-cli schedule remove <item_id>
```

| 命令 | 说明 |
|------|------|
| `schedule today` | 查看今天的学习计划 |
| `schedule daily <date>` | 查看指定日期的学习计划 |
| `schedule add <date> <type_id>` | 手动添加活动到某天 |
| `schedule complete <id> --note '...'` | 标记完成，可选附带完成备注 |
| `schedule uncomplete <id>` | 取消完成标记 |
| `schedule remove <id>` | 删除某天的活动 |

### 星星奖励 (`stars`)

```bash
mars-cli stars summary
mars-cli stars list [--date YYYY-MM-DD]
mars-cli stars add <stars> -a '<颁发者>' [-r '<原因>'] [--schedule-id <id>]
mars-cli stars redeem <star_id>
mars-cli stars delete <star_id>
```

| 命令 | 说明 |
|------|------|
| `stars summary` | 查看星星汇总（总数、可兑换金额、近期记录） |
| `stars list` | 查看星星记录列表 |
| `stars list --date 2025-07-10` | 查看某天的星星记录 |
| `stars add <数量> -a '<颁发者>'` | 颁发星星奖励 |
| `stars add 3 -a '妈妈' -r '作业优秀'` | 颁发 3 颗星并附原因 |
| `stars add 2 -a '爸爸' --schedule-id 12` | 颁发星星并关联学习计划项 |
| `stars redeem <id>` | 兑换星星 |
| `stars delete <id>` | 删除星星记录（撤回） |

## 常见使用场景

### 查看家庭服务器状态

```bash
mars-cli nodes list --table
mars-cli nodes exec home-server-01 'df -h && free -h' -t 15
```

### 管理家庭留言

```bash
mars-cli board list
mars-cli board add '今晚不回家吃饭' -a '小明' -c yellow
mars-cli board pin <message_id>
```

### 本周吃什么

```bash
# 查看当前菜单
mars-cli meals plan current

# AI 生成月度菜单（耗时较长）
mars-cli meals plan generate

# 手动加菜
mars-cli meals dishes list -q '红烧'
mars-cli meals plan add 2025-06-07 dinner 5
```

### 管理云盘文件

```bash
mars-cli drive list
mars-cli drive mkdir '备份' -p 3
mars-cli drive preview 'documents/notes.md'
mars-cli drive url 'photos/vacation.jpg' --expires 7200
```

### 视频学习管理

```bash
mars-cli videos list
mars-cli videos get 1
mars-cli videos process 1
mars-cli videos note 12 '## 关键要点\n- 要点1\n- 要点2'
mars-cli videos progress 12 --mastered 1
```

### 看板壁纸管理

```bash
# 从 Bing 每日壁纸 + Pexels 随机风景壁纸池中刷新，每次不重复
mars-cli dashboard refresh-wallpaper

# AI 生成高清风景壁纸，根据季节自动选择主题
mars-cli dashboard generate-wallpaper

# AI 生成自定义主题壁纸
mars-cli dashboard generate-wallpaper --prompt '星空下的雪山，宁静壮观'

# 列出所有已生成的 AI 壁纸
mars-cli dashboard list-wallpapers

# 设置指定壁纸为看板背景（文件名从 list-wallpapers 获取）
mars-cli dashboard set-wallpaper ai-wallpaper_高清风景壁纸,星空下的雪山,宁静壮观,_1781234567890.png
```

### 看板播报与翻页

```bash
# 语音播报留言板内容（默认）
mars-cli dashboard broadcast

# 语音播报今日菜谱
mars-cli dashboard broadcast --source meals

# 语音播报学习计划并自动切换到学习计划页
mars-cli dashboard broadcast --source schedule --page 1

# 播报自定义文本
mars-cli dashboard broadcast --source text --text '该收拾书包准备上学啦'

# 远程切换到学习计划页
mars-cli dashboard switch-page 1

# 启动自动轮播，每 60 秒在家庭看板和学习计划间切换
mars-cli dashboard switch-page 0 --auto-rotate --interval 60

# 立即进入屏保模式（仅展示壁纸背景）
mars-cli dashboard screensaver true

# 唤醒看板（恢复内容展示）
mars-cli dashboard screensaver false
```

### 管理儿童学习计划

```bash
# 查看今天的学习计划
mars-cli schedule today

# 标记作业完成并添加备注
mars-cli schedule complete 12 --note '数学作业全对，语文抄写认真'

# 查看本周活动类型
mars-cli schedule types list

# 新增一个自定义活动
mars-cli schedule types add '练钢琴' --icon '🎹' --color '#E91E63' --category arts

# 查看当前周模板
mars-cli schedule template get

# 设置周模板
mars-cli schedule template set '{"name":"默认","days":{"mon":[1,3],"tue":[2,4],"wed":[1],"thu":[3,5],"fri":[1],"sat":[2,4,5],"sun":[5]}}'

# 查看指定日期的计划
mars-cli schedule daily 2025-07-10

# 手动添加活动
mars-cli schedule add 2025-07-10 3
```

### 管理星星奖励

```bash
# 查看星星汇总（总数、可兑换金额、近期记录）
mars-cli stars summary

# 查看星星记录列表
mars-cli stars list

# 查看某天的星星记录
mars-cli stars list --date 2025-07-10

# 奖励 3 颗星星
mars-cli stars add 3 -a '妈妈' -r '数学作业全对'

# 奖励星星并关联学习计划项
mars-cli stars add 2 -a '爸爸' -r '读绘本很认真' --schedule-id 12

# 兑换星星
mars-cli stars redeem 5

# 删除星星记录（撤回误操作）
mars-cli stars delete 3
```

壁纸来源：Bing 每日精选（8张）+ Pexels 随机风景（15张，8种主题轮换）+ AI 生成（按季节主题自动选择，支持自定义提示词）。
AI 生成的壁纸持久保存在 OSS 目录 `/mnt/oss-sybuddy/data/wallpapers/`，可随时切换。

## 输出格式

所有命令默认输出 JSON 格式，便于程序解析。使用 `--table`（nodes list）或 `--no-json`（board list）可切换到表格/可读格式。

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| 无法连接到服务 | 地址错误或网络不通 | 检查 `MARS_SANDBOX_URL` 和网络 |
| 认证失败 (403) | API Key 无效 | 检查 `MARS_SANDBOX_API_KEY` |
| 未认证 (401) | 未配置认证信息 | 配置 API Key 或用户名密码 |
| 资源不存在 (404) | ID 错误 | 先用 list 命令确认 ID |
| 命令执行超时 (504) | 远程命令执行过久 | 增加 `-t` 超时值 |
| 未配置服务地址 | 缺少 URL 配置 | 通过任一方式配置 URL |
| 登录失败 | 用户名或密码错误 | 检查 `MARS_SANDBOX_USERNAME` / `MARS_SANDBOX_PASSWORD` |

## 注意事项

- `nodes exec` 是最常用的远程操作命令，可在节点上执行任意 shell 命令
- `meals plan generate` 耗时较长，建议设置足够的超时
- board/meals/videos/drive/schedule 等模块需要 Cookie 认证，配置了 username+password 后会自动登录
- 所有输出均为 JSON，方便 Agent 解析和呈现
- 使用 `mars-cli --help` 或 `mars-cli <module> --help` 查看完整帮助
