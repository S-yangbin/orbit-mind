---
name: amap-gui
description: >-
  高德地图智能操控 CLI。通过 amap-gui 命令行工具启动地图 GUI 容器，
  搜索兴趣点（POI）、规划路线（驾车/步行/骑行/公交）、控制地图视图状态。
  支持地名或坐标搜索、周边搜索、途经点规划、多种出行策略。
  当用户提到：地图、导航、路线规划、附近搜索、POI、怎么走、多远、
  驾车路线、公交地铁、骑行路线、步行导航、找餐厅、找加油站、
  查找附近、搜索地点、地图查看、看看某地的地图时触发。
  当用户问「从A到B怎么走」「附近有什么好吃的」「帮我规划路线」等
  地图相关问题时，也应触发本 Skill。
compatibility: Requires amap-gui installed (npm i -g @amap-lbs/amap-gui).
metadata:
  author: orbit-mind
  version: "1.0"
  tags: [map, navigation, poi, route-planning, amap, geocoding, transit, driving]
  category: location
required_environment_variables:
  - name: AMAP_KEY
    prompt: 高德地图 Web JS API Key
    help: >-
      在高德开放平台控制台（https://console.amap.com）注册开发者后，
      申请 Web 端（JS API）的 Key。
    required_for: 所有 amap-gui 命令（必填）
  - name: AMAP_SECURITY_KEY
    prompt: 高德地图安全密钥
    help: 与 AMAP_KEY 配对的安全密钥，在同一控制台获取。
    required_for: 所有 amap-gui 命令（必填）
---

# amap-gui — 高德地图智能操控

通过 `amap-gui` 命令行工具启动地图可视化容器，执行 POI 搜索、路线规划和地图状态控制，结果以 JSON 返回并在 GUI 地图上实时展示。

## 何时使用

当用户需要：
- 搜索某城市的餐厅、加油站、景点等兴趣点
- 查找某地周边的商铺、设施
- 规划两点之间的驾车/步行/骑行/公交路线
- 查看某地的地图、调整地图视角和样式
- 在地图上交互式点选目的地后规划导航

触发关键词：地图、导航、路线、怎么走、附近、POI、搜索地点、驾车、公交、地铁、骑行、步行、查找餐厅、加油站、咖啡馆

## 前提条件

### 检查 amap-gui 是否安装

```bash
amap-gui --help
```

如果未安装：
```bash
npm i -g @amap-lbs/amap-gui
```

### 配置 API Key（必填）

```bash
export AMAP_KEY=your_amap_web_js_key
export AMAP_SECURITY_KEY=your_amap_security_key
```

在高德开放平台控制台 https://console.amap.com 注册开发者并申请 Web 端（JS API）Key 和安全密钥。

## 功能模块总览

| 模块 | 命令 | 说明 |
|------|------|------|
| 地图生命周期 | `amap-gui start / stop / status` | 启动、关闭、检查地图容器 |
| 地图状态控制 | `amap-gui mapState` | 设置/获取中心点、缩放、旋转、俯仰、样式 |
| POI 搜索 | `amap-gui searchPOI` | 关键词搜索或周边搜索兴趣点 |
| 路线规划 | `amap-gui route` | 驾车/步行/骑行/公交路线规划 |
| 交互事件 | `amap-gui getLastEvent` | 获取用户在地图上的最后一次交互 |

## 命令参考

### start / stop / status — 地图生命周期

启动、关闭地图容器或检查运行状态。所有地图操作前需确保容器已启动。

```bash
amap-gui status        # 检查是否运行中
amap-gui start         # 启动容器（阻塞直到就绪）
amap-gui stop          # 关闭容器
```

### mapState — 地图状态控制

设置或获取地图视图参数：中心点、缩放级别、旋转角度、俯仰角度和样式。

```bash
# 获取当前状态
amap-gui mapState --action get

# 设置中心点和样式
amap-gui mapState --action set --center 116.397,39.909 --zoom 15 --style dark

# 设置俯仰角（3D 效果）
amap-gui mapState --action set --center 121.491,31.233 --zoom 15 --pitch 45 --style dark
```

| 参数 | 说明 |
|------|------|
| `--action` | `get`（默认）或 `set` |
| `--center` | 中心点坐标 `lng,lat` |
| `--zoom` | 缩放级别 3-20 |
| `--rotation` | 旋转角度 0-360 |
| `--pitch` | 俯仰角度 0-83 |
| `--style` | 地图样式（见下方列表） |

**可用样式：** `normal`、`dark`、`light`、`whitesmoke`、`fresh`、`grey`、`graffiti`、`macaron`、`blue`、`darkblue`、`wine`

也可用 `--json` 传入完整 JSON（优先级最高）：
```bash
amap-gui mapState --json '{"action":"set","center":"116.397,39.909","zoom":15,"style":"dark"}'
```

### searchPOI — POI 搜索

关键词搜索或周边搜索兴趣点，返回名称、地址、坐标、电话、图片等信息。

```bash
# 城市内关键词搜索
amap-gui searchPOI --keyword 星巴克 --city 北京

# 周边搜索（坐标 + 半径）
amap-gui searchPOI --keyword 咖啡 --center 120.155,30.274 --radius 1000

# 指定返回数量
amap-gui searchPOI --keyword 火锅 --city 成都 --pageSize 5 --pageIndex 1
```

| 参数 | 说明 |
|------|------|
| `--keyword` | 搜索关键词（必填） |
| `--city` | 搜索城市名 |
| `--center` | 周边搜索中心坐标 `lng,lat`（仅坐标格式） |
| `--radius` | 搜索半径（米），默认 3000 |
| `--pageSize` | 每页数量，默认 10 |
| `--pageIndex` | 页码，默认 1 |

搜索结果 JSON 结构：
```json
{
  "success": true,
  "data": {
    "pois": [
      {
        "id": "B0FFJGCM9X",
        "name": "星巴克(京汇大厦店)",
        "type": "餐饮服务;咖啡厅;星巴克咖啡",
        "location": [116.462991, 39.906998],
        "address": "建国路乙118号京汇大厦一层",
        "tel": "010-65685868",
        "photo": "https://..."
      }
    ],
    "total": 600
  }
}
```

### route — 路线规划

支持驾车、步行、骑行、公交四种出行方式。起点和终点支持地名或坐标。

```bash
# 驾车路线
amap-gui route --from 北京南站 --to 首都机场T3 --type driving

# 公交路线（需指定城市）
amap-gui route --from 北京站 --to 中关村 --type transit --city 北京

# 步行路线
amap-gui route --from 王府井 --to 116.397029,39.917839 --to-name 故宫博物院 --type walking

# 驾车带途经点和策略
amap-gui route --from 上海人民广场 --to 杭州西湖 --type driving --waypoints "嘉兴+桐乡" --policy fastest
```

| 参数 | 说明 |
|------|------|
| `--from` | 起点（地名或 `lng,lat` 坐标）（必填） |
| `--from-name` | 起点显示名称（配合坐标使用） |
| `--to` | 终点（地名或 `lng,lat` 坐标）（必填） |
| `--to-name` | 终点显示名称（配合坐标使用） |
| `--type` | 出行方式：`driving` / `walking` / `riding` / `transit`（必填） |
| `--waypoints` | 途经点，加号分隔（仅 driving，最多 16 个） |
| `--policy` | 驾车策略（见下方） |
| `--strategy` | 公交策略（见下方） |
| `--city` | 城市名（transit 模式必填） |

**驾车策略：** `fastest`（最快）· `least_fee`（最省钱）· `shortest`（最短）· `no_highway`（不走高速）· `avoid_jam`（躲避拥堵）

**公交策略：** `fastest`（最快）· `least_cost`（最经济）· `least_walk`（少步行）· `most_comfort`（最舒适）· `no_subway`（不坐地铁）

路线结果 JSON 结构：
```json
{
  "success": true,
  "data": {
    "summary": {
      "distance": 2090,
      "time": 391,
      "steps": [
        {
          "instruction": "沿北四环西路辅路向东行驶474米左转调头",
          "road": "北四环西路辅路",
          "distance": 474,
          "time": 119,
          "action": "左转调头"
        }
      ],
      "tolls": 0
    }
  }
}
```

### getLastEvent — 获取用户交互事件

获取用户在地图 GUI 上的最后一次交互操作，用于响应用户点选。

```bash
amap-gui getLastEvent
```

| 事件类型 | 触发方式 | 返回字段 |
|----------|----------|----------|
| `map_click` | 点击地图空白处 | `position` |
| `poi_click` | 点击地图上的 POI 标记 | `title` + `address` + `position` |
| `poi_select` | 在搜索结果列表中选中 | `title` + `address` + `position` |

## 常见使用场景

### 查找附近美食

```bash
amap-gui start
amap-gui searchPOI --keyword 火锅 --center 104.065,30.572 --radius 2000 --pageSize 5
```

### 从 A 到 B 驾车导航

```bash
amap-gui start
amap-gui route --from 北京南站 --to 首都机场T3 --type driving --policy avoid_jam
```

### 公交出行规划

```bash
amap-gui start
amap-gui route --from 北京站 --to 中关村 --type transit --city 北京 --strategy least_walk
```

### 搜索后导航（连续操作）

```bash
# 1. 搜索目的地
amap-gui searchPOI --keyword 故宫博物院 --city 北京

# 2. 从结果中取坐标，规划步行路线
amap-gui route --from 王府井 --to 116.397029,39.917839 --to-name 故宫博物院 --type walking
```

### 用户点选地图后导航

```bash
# 用户在地图上点选了目的地
amap-gui getLastEvent
# → position: [116.488778, 40.002995], title: "某餐厅"

# 用坐标规划路线
amap-gui route --from 北京站 --to 116.488778,40.002995 --to-name 某餐厅 --type driving
```

### 查看某地地图并调整视角

```bash
amap-gui start
amap-gui mapState --action set --center 121.491,31.233 --zoom 15 --pitch 45 --style dark
```

### 完成后停止

```bash
amap-gui stop
```

## 输出格式

所有命令输出 JSON 到 stdout，结构统一为：
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

失败时 `success` 为 `false`，`error` 包含错误信息。

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| `amap-gui: command not found` | 未安装 CLI | 运行 `npm i -g @amap-lbs/amap-gui` |
| GUI not running | 未启动容器 | 先运行 `amap-gui start` |
| Key 相关错误 | 未配置或 Key 无效 | 检查 `AMAP_KEY` 和 `AMAP_SECURITY_KEY` 环境变量 |
| 搜索无结果 | 关键词或范围过窄 | 放宽搜索条件或换关键词 |
| transit 模式报错 | 未指定 `--city` | 公交模式必须加 `--city 城市名` |

## 注意事项

- 所有操作前需 `amap-gui start` 启动容器
- `--json` 参数优先级最高，会覆盖其他命令行参数
- 坐标格式为 `lng,lat`（经度在前，纬度在后）
- `--waypoints` 用加号 `+` 分隔多个途经点（仅驾车模式，最多 16 个）
- 公交模式（transit）必须指定 `--city` 参数
- 周边搜索 `--center` 仅支持坐标格式，不支持地名
- 使用完毕后建议 `amap-gui stop` 关闭容器释放资源
