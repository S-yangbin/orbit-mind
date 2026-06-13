---
name: flyai
description: >-
  飞猪旅行 AI 搜索与规划。通过 flyai CLI 调用飞猪 MCP 服务，
  搜索机票、火车票、酒店、景点门票、度假套餐等全品类旅行商品，
  支持自然语言搜索和 AI 语义理解，返回含价格和预订链接的结构化结果。
  当用户提到：旅游、旅行、出行、度假、机票、火车票、酒店、民宿、景点、
  门票、周末去哪玩、假期规划、行程安排、亲子游、自驾游时触发。
  当用户问「XX城市有什么好玩的」「从A到B怎么走最划算」「找个亲子酒店」等
  旅行相关问题时，也应触发本 Skill。
compatibility: Requires flyai-cli installed (npm i -g @fly-ai/flyai-cli).
metadata:
  author: orbit-mind
  version: "1.0"
  tags: [travel, flight, hotel, poi, trip-planning, fliggy, search]
  category: travel
required_environment_variables:
  - name: FLYAI_API_KEY
    prompt: FlyAI API Key
    help: >-
      在飞猪 AI 开放平台控制台获取（https://flyai.open.fliggy.com/console）。
      不设也可使用，但结果质量可能受限；设置后可获得更充足的调用次数和稳定服务。
    required_for: 所有 flyai 命令（可选，推荐配置）
---

# flyai — 飞猪旅行 AI 搜索与规划

通过 `flyai` 命令行工具搜索飞猪全品类旅行商品，包括机票、火车票、酒店、景点门票、度假套餐等，返回含价格和预订链接的结构化 JSON 结果。

## 何时使用

当用户需要：
- 搜索或比较机票、火车票
- 查找目的地酒店、民宿
- 了解某城市的景点和活动
- 规划周末或假期行程
- 查找亲子游、度假套餐
- 查询万豪集团旗下酒店或套餐
- 用自然语言描述旅行需求并获取 AI 推荐

触发关键词：旅游、旅行、出行、度假、机票、火车票、高铁、酒店、民宿、住宿、景点、门票、周末去哪玩、假期规划、行程安排、亲子游、自驾游、万豪、Marriott

## 前提条件

### 检查 flyai 是否安装

```bash
flyai --help
```

如果未安装：
```bash
npm i -g @fly-ai/flyai-cli
```

### 配置 API Key（推荐）

```bash
flyai config set FLYAI_API_KEY "your-key"
```

API Key 在 https://flyai.open.fliggy.com/console 获取。不设也可使用，设置后结果更丰富、调用更稳定。

## 功能模块总览

| 模块 | 命令 | 说明 |
|------|------|------|
| 全域搜索 | `flyai keyword-search` | 自然语言跨品类搜索（机票/酒店/门票/度假等） |
| AI 语义搜索 | `flyai ai-search` | AI 理解复杂意图的语义搜索 |
| 机票搜索 | `flyai search-flight` | 结构化航班搜索，支持舱位/价格/时间筛选 |
| 火车票搜索 | `flyai search-train` | 结构化火车票搜索，支持席别/价格筛选 |
| 酒店搜索 | `flyai search-hotel` | 按目的地搜索酒店，支持星级/床型/价格/景点附近 |
| 景点搜索 | `flyai search-poi` | 按城市搜索景点和活动，支持分类/等级筛选 |
| 万豪酒店 | `flyai search-marriott-hotel` | 万豪集团旗下酒店搜索 |
| 万豪套餐 | `flyai search-marriott-package` | 万豪酒店套餐（下午茶、SPA等） |

## 命令参考

### keyword-search — 全域搜索

一句话搜索所有旅行品类：酒店、机票、火车票、门票、度假、邮轮、签证、电话卡等。

```bash
flyai keyword-search --query "杭州三日游"
flyai keyword-search --query "三亚亲子酒店"
flyai keyword-search --query "法国签证"
flyai keyword-search --query "上海出发邮轮"
```

| 参数 | 说明 |
|------|------|
| `--query` | 自然语言查询（必填） |

### ai-search — AI 语义搜索

理解复杂意图的语义搜索，支持酒店、景点、机票、火车票及混合查询。适合描述预算、人数、偏好等复杂场景。

```bash
flyai ai-search --query "五一杭州3天游，预算每人2000，想住西湖附近"
flyai ai-search --query "下周上海直飞东京，找性价比高的航班和酒店"
flyai ai-search --query "带娃周末去湖州，要儿童设施丰富且交通方便的酒店"
```

| 参数 | 说明 |
|------|------|
| `--query` | 自然语言查询（必填），可包含预算、偏好、人数等 |

### search-flight — 机票搜索

结构化航班搜索，支持单程/往返、舱位、价格上限、时间范围等精细筛选。

```bash
# 基础单程搜索
flyai search-flight --origin "北京" --destination "上海" --dep-date 2026-07-01

# 往返、直飞、按价格从低到高排序
flyai search-flight \
  --origin "上海" --destination "东京" \
  --dep-date 2026-07-20 --back-date 2026-07-25 \
  --journey-type 1 --sort-type 3

# 5月北京到曼谷最便宜的直飞
flyai search-flight \
  --origin "北京" --destination "曼谷" \
  --dep-date-start 2026-05-01 --dep-date-end 2026-05-31 \
  --journey-type 1 --sort-type 3
```

| 参数 | 说明 |
|------|------|
| `--origin` | 出发城市或机场（必填） |
| `--destination` | 到达城市或机场 |
| `--dep-date` | 出发日期（YYYY-MM-DD） |
| `--dep-date-start` / `--dep-date-end` | 出发日期范围 |
| `--back-date` | 返程日期 |
| `--back-date-start` / `--back-date-end` | 返程日期范围 |
| `--journey-type` | `1` = 直飞，`2` = 中转 |
| `--seat-class-name` | 舱位名称（经济舱/商务舱/头等舱） |
| `--transport-no` | 航班号 |
| `--transfer-city` | 中转城市 |
| `--dep-hour-start` / `--dep-hour-end` | 出发时间范围（小时） |
| `--arr-hour-start` / `--arr-hour-end` | 到达时间范围（小时） |
| `--total-duration-hour` | 最大飞行时长（小时） |
| `--max-price` | 价格上限（元） |
| `--sort-type` | `1` 价格降序 · `2` 推荐 · `3` 价格升序 · `4` 时长升序 · `5` 时长降序 · `6` 早出发 · `7` 晚出发 · `8` 直飞优先 |

### search-train — 火车票搜索

结构化火车票搜索，支持单程/往返、席别、价格上限等筛选。

```bash
# 基础搜索
flyai search-train --origin "北京" --destination "上海" --dep-date 2026-07-01

# 直达、二等座、按价格从低到高
flyai search-train \
  --origin "上海" --destination "杭州" \
  --dep-date 2026-07-20 --journey-type 1 \
  --seat-class-name "二等座" --sort-type 3
```

| 参数 | 说明 |
|------|------|
| `--origin` | 出发城市或车站（必填） |
| `--destination` | 到达城市或车站 |
| `--dep-date` | 出发日期（YYYY-MM-DD） |
| `--dep-date-start` / `--dep-date-end` | 出发日期范围 |
| `--back-date` | 返程日期 |
| `--back-date-start` / `--back-date-end` | 返程日期范围 |
| `--journey-type` | `1` = 直达，`2` = 中转 |
| `--seat-class-name` | 席别：二等座 · 一等座 · 商务座 · 硬卧 · 软卧 |
| `--transport-no` | 车次（多个用逗号分隔） |
| `--transfer-city` | 中转城市（多个用逗号分隔） |
| `--dep-hour-start` / `--dep-hour-end` | 出发时间范围（24小时制） |
| `--arr-hour-start` / `--arr-hour-end` | 到达时间范围（24小时制） |
| `--total-duration-hour` | 最大行程时长（小时） |
| `--max-price` | 价格上限（元） |
| `--sort-type` | 同机票排序（`1`-`8`） |

### search-hotel — 酒店搜索

按目的地搜索酒店、民宿、客栈，支持星级、床型、价格、景点附近等筛选。

```bash
# 杭州西湖附近酒店
flyai search-hotel \
  --dest-name "杭州" --poi-name "西湖" \
  --check-in-date 2026-07-10 --check-out-date 2026-07-12

# 三亚4-5星酒店，800元以内，按评分排序
flyai search-hotel \
  --dest-name "三亚" --hotel-stars "4,5" \
  --sort rate_desc --max-price 800

# 亲子民宿
flyai search-hotel \
  --dest-name "莫干山" --hotel-types "民宿" \
  --key-words "亲子" --check-in-date 2026-07-15
```

| 参数 | 说明 |
|------|------|
| `--dest-name` | 目的地：国家/省/市/区（必填） |
| `--key-words` | 搜索关键词 |
| `--poi-name` | 附近景点名称 |
| `--hotel-types` | 类型：酒店 · 民宿 · 客栈 |
| `--sort` | 排序：`distance_asc` · `rate_desc` · `price_asc` · `price_desc` · `no_rank` |
| `--check-in-date` | 入住日期（YYYY-MM-DD） |
| `--check-out-date` | 退房日期（YYYY-MM-DD） |
| `--hotel-stars` | 星级（1-5，逗号分隔） |
| `--hotel-bed-types` | 床型：大床房 · 双床房 · 多床房 |
| `--max-price` | 每晚价格上限（元） |

### search-poi — 景点与活动搜索

按城市搜索景点门票、一日游、户外活动等，支持分类和等级筛选。

```bash
# 西安历史古迹
flyai search-poi --city-name "西安" --category "历史古迹"

# 北京5A景点
flyai search-poi --city-name "北京" --poi-level 5

# 杭州西湖周边山湖田园
flyai search-poi --city-name "杭州" --keyword "西湖" --category "山湖田园"

# 上海主题乐园
flyai search-poi --city-name "上海" --category "主题乐园"
```

| 参数 | 说明 |
|------|------|
| `--city-name` | 城市名称（必填） |
| `--keyword` | 景点名称关键词 |
| `--poi-level` | 景点等级（1-5） |
| `--category` | 分类（见下方列表） |

**可用分类：**
- 自然风光：`自然风光`、`山湖田园`、`森林丛林`、`峡谷瀑布`、`沙滩海岛`、`沙漠草原`
- 人文历史：`人文古迹`、`古镇古村`、`历史古迹`、`园林花园`、`宗教场所`
- 乐园场馆：`公园乐园`、`主题乐园`、`水上乐园`、`影视基地`、`动物园`、`植物园`、`海洋馆`
- 文体活动：`体育场馆`、`演出赛事`、`剧院剧场`、`博物馆`、`纪念馆`、`展览馆`、`地标建筑`
- 生活体验：`市集`、`文创街区`、`城市观光`
- 户外活动：`户外活动`、`滑雪`、`漂流`、`冲浪`、`潜水`、`露营`、`温泉`

### search-marriott-hotel — 万豪酒店搜索

搜索万豪集团旗下酒店（万豪、喜来登、威斯汀、丽思卡尔顿等）。

```bash
# 上海万豪系酒店
flyai search-marriott-hotel \
  --dest-name "上海" --hotel-brands "JW Marriott,Sheraton" \
  --check-in-date 2026-07-10 --check-out-date 2026-07-12

# 杭州万豪酒店，1200以内，按价格排序
flyai search-marriott-hotel \
  --dest-name "杭州" --sort price_asc --max-price 1200
```

| 参数 | 说明 |
|------|------|
| `--dest-name` | 目的地（必填） |
| `--key-words` | 搜索关键词 |
| `--poi-name` | 附近景点名称 |
| `--hotel-brands` | 万豪品牌（逗号分隔） |
| `--hotel-name` | 酒店名称（精确或模糊） |
| `--hotel-bed-types` | 床型：大床房 · 双床房 · 多床房 |
| `--max-price` | 每晚价格上限（元） |
| `--sort` | 排序：`distance_asc` · `rate_desc` · `price_asc` · `price_desc` · `no_rank` |
| `--check-in-date` | 入住日期（YYYY-MM-DD） |
| `--check-out-date` | 退房日期（YYYY-MM-DD） |

### search-marriott-package — 万豪套餐搜索

搜索万豪酒店套餐和打包优惠（下午茶、SPA套餐等）。

```bash
# 上海万豪套餐
flyai search-marriott-package --keyword "上海"

# JW万豪套餐，按价格排序
flyai search-marriott-package --keyword "JW Marriott" --sort-type price_asc
```

| 参数 | 说明 |
|------|------|
| `--keyword` | 搜索关键词：省/市/品牌/酒店名/卖点（必填） |
| `--sort-type` | 排序：`price_asc` · `price_desc` |

## 常见使用场景

### 周末亲子出行规划

```bash
# 搜索湖州亲子酒店
flyai ai-search --query "周末带娃去湖州两天，要儿童设施丰富交通方便的酒店"

# 补充搜索周边景点
flyai search-poi --city-name "湖州" --category "主题乐园"
```

### 假期旅行全链路规划

```bash
# 1. AI 搜索整体推荐
flyai ai-search --query "暑假一家三口去三亚5天，预算每人3000，想住海边酒店"

# 2. 搜索机票
flyai search-flight \
  --origin "上海" --destination "三亚" \
  --dep-date 2026-07-15 --back-date 2026-07-20 \
  --sort-type 3

# 3. 搜索酒店
flyai search-hotel \
  --dest-name "三亚" --poi-name "亚龙湾" \
  --hotel-stars "4,5" --check-in-date 2026-07-15 --check-out-date 2026-07-20 \
  --sort rate_desc

# 4. 搜索景点活动
flyai search-poi --city-name "三亚" --category "沙滩海岛"
```

### 找便宜机票

```bash
# 5月北京到曼谷最便宜直飞
flyai search-flight \
  --origin "北京" --destination "曼谷" \
  --dep-date-start 2026-05-01 --dep-date-end 2026-05-31 \
  --journey-type 1 --sort-type 3

# 高铁对比
flyai search-train \
  --origin "上海" --destination "杭州" \
  --dep-date 2026-07-01 --journey-type 1 \
  --seat-class-name "二等座" --sort-type 3
```

### 团队出行酒店对比

```bash
# 三亚4星双床房，500以内，按评分排序
flyai search-hotel \
  --dest-name "三亚" --hotel-stars 4 \
  --hotel-bed-types "双床房" --max-price 500 --sort rate_desc
```

### 万豪度假套餐

```bash
# 搜索上海万豪下午茶套餐
flyai search-marriott-package --keyword "上海" --sort-type price_asc

# 搜索某品牌酒店
flyai search-marriott-hotel \
  --dest-name "三亚" --hotel-brands "Ritz-Carlton" \
  --check-in-date 2026-08-01 --check-out-date 2026-08-05
```

## 输出格式

所有命令输出单行 JSON 到 stdout，错误和提示信息输出到 stderr。结果中包含商品名称、价格、图片、评分和预订链接（detailUrl）等结构化信息，便于 Agent 解析和呈现给用户。

## 旅行场景覆盖

| 类别 | 示例 |
|------|------|
| 交通 | 机票、火车票、接送机、租车、包车 |
| 住宿 | 酒店、民宿、客栈、机+酒套餐 |
| 体验 | 景点门票、一日游、跟团游、定制游 |
| 活动 | 演唱会、体育赛事、演出、动漫展 |
| 服务 | 签证、旅游保险、电话卡、WiFi租赁 |
| 行程 | 邮轮、周末游、蜜月、亲子游、研学游 |

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| `flyai: command not found` | 未安装 CLI | 运行 `npm i -g @fly-ai/flyai-cli` |
| 空结果或结果较少 | 查询条件过于严格 | 放宽筛选条件（如扩大日期范围、提高价格上限） |
| API Key 相关提示 | 未配置或 Key 过期 | 到控制台重新获取并设置 |
| 网络错误 | 网络连接问题 | 检查网络连接 |

## 注意事项

- 所有搜索结果实时来自飞猪官方商品库，价格和库存为当前最新数据
- `ai-search` 最适合复杂场景，能理解预算、人数、偏好等自然语言描述
- `keyword-search` 适合快速全域探索，一次查询覆盖所有品类
- 对于精确比较需求（如指定日期/舱位/星级），使用对应的结构化搜索命令
- 每个结果都包含 `detailUrl` 预订链接，用户可直接跳转飞猪下单
- 组合使用多个命令可生成完整的行程规划方案
