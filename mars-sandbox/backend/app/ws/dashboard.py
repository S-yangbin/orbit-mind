"""
Dashboard WebSocket handler
推送家庭看板实时数据（食谱、旅游、留言、天气、壁纸）到前端
"""

import asyncio
import json
import logging
import time
import requests
from datetime import datetime, date, timedelta
from typing import Set, Optional

from starlette.websockets import WebSocket, WebSocketDisconnect

from ..database import SessionLocal
from ..models import (
    BoardMessage, Page, MealPlan, MealPlanItem, MealLog, Dish, FamilyMember
)
from ..config import settings

logger = logging.getLogger(__name__)

# 全局 dashboard WebSocket 连接集合
_dashboard_connections: Set[WebSocket] = set()
_lock = asyncio.Lock()

# 缓存：天气（30分钟）、壁纸（1小时）
_weather_cache: dict = {"data": None, "timestamp": 0}
_weather_forecast_cache: dict = {"data": None, "timestamp": 0}
_background_cache: dict = {"data": None, "timestamp": 0}

WEATHER_CACHE_TTL = 30 * 60  # 30分钟
WEATHER_FORECAST_CACHE_TTL = 60 * 60  # 1小时
BACKGROUND_CACHE_TTL = 60 * 60  # 1小时


async def register_dashboard(ws: WebSocket):
    async with _lock:
        _dashboard_connections.add(ws)
    logger.info("Dashboard WS 连接建立，当前连接数: %d", len(_dashboard_connections))


async def unregister_dashboard(ws: WebSocket):
    async with _lock:
        _dashboard_connections.discard(ws)
    logger.info("Dashboard WS 连接关闭，当前连接数: %d", len(_dashboard_connections))


async def broadcast_to_dashboards(msg: dict):
    """向所有 dashboard 连接广播消息"""
    if not _dashboard_connections:
        return
    payload = json.dumps(msg, ensure_ascii=False, default=str)
    dead: list[WebSocket] = []
    async with _lock:
        for ws in _dashboard_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            _dashboard_connections.discard(ws)


def _get_board_messages(db) -> list[dict]:
    """获取所有未过期的留言"""
    today = date.today()
    messages = (
        db.query(BoardMessage)
        .filter(
            (BoardMessage.expires_at == None) | (BoardMessage.expires_at >= today)
        )
        .order_by(BoardMessage.pinned.desc(), BoardMessage.created_at.desc())
        .all()
    )
    return [
        {
            "id": m.id,
            "content": m.content,
            "author": m.author,
            "color": m.color,
            "pinned": m.pinned,
            "expires_at": m.expires_at.isoformat() if m.expires_at else None,
            "acknowledged_by": _parse_acknowledged_by(m),
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


def _parse_acknowledged_by(msg: BoardMessage) -> list:
    """解析留言已确认成员 JSON 字段"""
    if msg.acknowledged_by is None:
        return []
    if isinstance(msg.acknowledged_by, list):
        return msg.acknowledged_by
    try:
        return json.loads(msg.acknowledged_by) or []
    except (json.JSONDecodeError, TypeError):
        return []


def _parse_json_field(value) -> list | dict | None:
    """安全解析 JSON 字段"""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _get_meal_plans(db) -> list[dict]:
    """
    获取前2周 + 后2周的食谱，仅筛选周六、周日
    与 meals 模块的周末菜单逻辑一致：
    - 有用餐记录(MealLog)的日期显示实际吃的菜品
    - 无记录的日期显示计划菜品
    """
    today = date.today()
    # 前2周的周一
    monday = today - timedelta(days=today.weekday())
    start_monday = monday - timedelta(weeks=2)
    # 后2周结束的周一（共约5周）
    end_monday = monday + timedelta(weeks=3)

    plans = (
        db.query(MealPlan)
        .filter(
            MealPlan.week_start_date >= start_monday,
            MealPlan.week_start_date < end_monday
        )
        .order_by(MealPlan.week_start_date)
        .all()
    )

    # 获取过去到今天的所有用餐记录（用于替换计划数据）
    four_weeks_ago = today - timedelta(weeks=2)
    meal_logs = (
        db.query(MealLog)
        .filter(MealLog.date >= four_weeks_ago, MealLog.date <= today)
        .order_by(MealLog.date)
        .all()
    )

    # Build meal_log lookup: date -> {meal_type -> [log, ...]}
    log_lookup: dict = {}
    for log in meal_logs:
        if log.date not in log_lookup:
            log_lookup[log.date] = {}
        log_lookup[log.date].setdefault(log.meal_type, []).append(log)

    # 收集所有需要查询照片的 dish_id
    all_dish_ids = set()
    for plan in plans:
        for item in plan.items:
            if item.date and item.date.weekday() in (5, 6) and item.dish_id:
                all_dish_ids.add(item.dish_id)

    # 批量查询每个 dish_id 的最近一张 meal_log 照片
    dish_photo_map = _batch_get_dish_photos(db, all_dish_ids)

    result = []
    processed_slots = set()  # (date, meal_type) already handled by logs

    for plan in plans:
        items = []
        for item in plan.items:
            # 仅筛选周六、周日（weekday 5=周六, 6=周日）
            if not item.date or item.date.weekday() not in (5, 6):
                continue

            # 有用餐记录的日期（含今天），跳过计划项（后面用 log 替代）
            if item.date <= today and item.date in log_lookup:
                processed_slots.add((item.date, item.meal_type))
                continue

            dish = item.dish
            items.append({
                "id": item.id,
                "date": item.date.isoformat(),
                "meal_type": item.meal_type,
                "dish": {
                    "id": dish.id,
                    "name": dish.name,
                    "category": dish.category or "",
                    "photo": dish_photo_map.get(dish.id),
                },
                "sort_order": item.sort_order,
                "is_manual": item.is_manual,
            })

        if items:
            result.append({
                "id": plan.id,
                "week_start_date": plan.week_start_date.isoformat() if plan.week_start_date else None,
                "status": plan.status,
                "items": items,
            })

    # 为有 meal_log 的日期生成实际菜品条目
    for log_date, meal_types in log_lookup.items():
        # 仅处理周末日期
        if log_date.weekday() not in (5, 6):
            continue

        for meal_type, logs in meal_types.items():
            seen_dish_ids = set()
            log_items = []
            dish_idx = 0
            for log in logs:
                dishes = _parse_json_field(log.dishes_json) or []
                for d in dishes:
                    if not isinstance(d, dict) or "name" not in d:
                        continue
                    dish_id = d.get("dish_id")
                    dish_obj = None
                    if dish_id:
                        dish_obj = db.query(Dish).filter(Dish.id == dish_id).first()
                    if not dish_obj:
                        dish_obj = db.query(Dish).filter(Dish.name == d["name"]).first()
                    if not dish_obj or dish_obj.id in seen_dish_ids:
                        continue
                    seen_dish_ids.add(dish_obj.id)
                    log_items.append({
                        "id": -(log.id * 100 + dish_idx),
                        "date": log_date.isoformat(),
                        "meal_type": meal_type,
                        "dish": {
                            "id": dish_obj.id,
                            "name": dish_obj.name,
                            "category": dish_obj.category or "其他",
                            "photo": log.image_path if dish_idx == 0 else dish_photo_map.get(dish_obj.id),
                        },
                        "sort_order": dish_idx,
                        "is_manual": 0,
                    })
                    dish_idx += 1

            if log_items:
                week_monday = log_date - timedelta(days=log_date.weekday())
                existing = next(
                    (r for r in result
                     if r.get("week_start_date") == week_monday.isoformat()),
                    None
                )
                if existing:
                    # 移除计划中同日同餐类型的条目，用实际数据替代
                    existing["items"] = [
                        i for i in existing["items"]
                        if not (i["date"] == log_date.isoformat()
                                and i["meal_type"] == meal_type)
                    ]
                    existing["items"].extend(log_items)
                else:
                    result.append({
                        "id": -week_monday.toordinal(),
                        "week_start_date": week_monday.isoformat(),
                        "status": "log",
                        "items": log_items,
                    })

    # 按 week_start_date 排序
    result.sort(key=lambda x: x.get("week_start_date", ""))
    return result


def _batch_get_dish_photos(db, dish_ids: set) -> dict:
    """
    批量查询每个 dish_id 最近的一张用餐照片。
    返回 {dish_id: image_path}
    """
    if not dish_ids:
        return {}

    photo_map = {}
    # 获取所有包含这些 dish_id 的 meal_log（最近3个月）
    three_months_ago = date.today() - timedelta(days=90)
    recent_logs = (
        db.query(MealLog)
        .filter(MealLog.date >= three_months_ago)
        .order_by(MealLog.date.desc())
        .all()
    )

    for log in recent_logs:
        dishes = _parse_json_field(log.dishes_json) or []
        for d in dishes:
            if not isinstance(d, dict):
                continue
            did = d.get("dish_id")
            if did and did in dish_ids and did not in photo_map:
                photo_map[did] = log.image_path

        # 如果所有 dish_id 都找到了，提前退出
        if len(photo_map) >= len(dish_ids):
            break

    return photo_map


def _get_recent_meals(db) -> list[dict]:
    """获取最近 7 天的用餐记录"""
    today = date.today()
    start = today - timedelta(days=7)
    logs = (
        db.query(MealLog)
        .filter(MealLog.date >= start, MealLog.date <= today)
        .order_by(MealLog.date.desc())
        .all()
    )
    result = []
    for log in logs:
        dishes = []
        if log.dishes_json:
            try:
                dishes = json.loads(log.dishes_json) if isinstance(log.dishes_json, str) else log.dishes_json
            except (json.JSONDecodeError, TypeError):
                dishes = []
        result.append({
            "id": log.id,
            "date": log.date.isoformat() if log.date else None,
            "meal_type": log.meal_type,
            "image_path": log.image_path,
            "dishes": dishes,
        })
    return result


def _get_travel_pages(db) -> list[dict]:
    """获取旅游相关页面（category=life）"""
    pages = (
        db.query(Page)
        .filter(Page.category == "life")
        .order_by(Page.updated_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": p.id,
            "slug": p.slug,
            "title": p.custom_title or p.scanned_title or p.title or p.slug,
            "description": p.custom_description or p.scanned_description or p.description or "",
            "thumbnail": p.thumbnail,
            "entry_file": p.entry_file,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in pages
    ]


def _get_family_members(db) -> list[dict]:
    """获取所有家庭成员（用于看板留言确认）"""
    members = db.query(FamilyMember).order_by(FamilyMember.id).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "avatar": m.avatar,
            "board_color": m.board_color,
        }
        for m in members
    ]


# wttr.in 天气代码 -> OpenWeatherMap icon 代码映射
_WTTR_TO_OWM_ICON = {
    "113": "01d", "116": "02d", "119": "03d", "122": "04d",
    "143": "50d", "176": "10d", "179": "13d", "182": "13d",
    "185": "13d", "200": "11d", "227": "13d", "230": "13d",
    "248": "50d", "260": "50d", "263": "09d", "266": "09d",
    "281": "13d", "284": "13d", "293": "10d", "296": "10d",
    "299": "10d", "302": "10d", "305": "10d", "308": "10d",
    "311": "13d", "314": "13d", "317": "13d", "320": "13d",
    "323": "13d", "326": "13d", "329": "13d", "332": "13d",
    "335": "13d", "338": "13d", "350": "13d", "353": "09d",
    "356": "10d", "359": "10d", "362": "13d", "365": "13d",
    "368": "13d", "371": "13d", "374": "13d", "377": "13d",
    "386": "11d", "389": "11d", "392": "11d", "395": "13d",
}


def _wttr_icon(code: str, is_day: bool = True) -> str:
    """wttr.in 天气代码转 OpenWeatherMap icon"""
    base = _WTTR_TO_OWM_ICON.get(code, "01d")
    if not is_day:
        base = base.replace("d", "n")
    return base


# wttr.in 天气代码 -> 中文描述（API 返回英文时兑底）
_WTTR_ZH_DESC = {
    "113": "晴", "116": "多云", "119": "阴", "122": "阴天",
    "143": "薄雾", "176": "局部小雨", "179": "局部小雪",
    "182": "雨夹雪", "185": "冻雨", "200": "雷阵雨",
    "227": "扬雪", "230": "暴雪", "248": "雾", "260": "冻雾",
    "263": "毛毛雨", "266": "小雨", "281": "冻毛毛雨",
    "284": "冻雨", "293": "局部小雨", "296": "小雨",
    "299": "中雨", "302": "大雨", "305": "大雨", "308": "暴雨",
    "311": "冻雨", "314": "雨夹雪", "317": "雨夹雪", "320": "小雪",
    "323": "局部小雪", "326": "小雪", "329": "中雪", "332": "大雪",
    "335": "大雪", "338": "暴雪", "350": "冰粒", "353": "阵雨",
    "356": "大雨", "359": "暴雨", "362": "雨夹雪", "365": "雨夹雪",
    "368": "阵雪", "371": "中雪", "374": "冰粒", "377": "冰粒",
    "386": "雷阵雨", "389": "雷暴雨", "392": "雷阵雪", "395": "雪",
}


def _wttr_desc_zh(code: str, api_desc: str) -> str:
    """获取中文天气描述，优先 API 返回，兑底本地映射"""
    if api_desc and not any(c.isascii() and c.isalpha() for c in api_desc):
        return api_desc
    return _WTTR_ZH_DESC.get(code, api_desc)


def _get_weather_from_wttr() -> Optional[dict]:
    """
    wttr.in fallback：当前天气
    支持中文城市名，无需 API Key
    """
    try:
        url = f"https://wttr.in/{settings.WEATHER_CITY}?format=j1"
        resp = requests.get(url, headers={"User-Agent": "mars-sandbox/1.0"}, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        curr = data.get("current_condition", [{}])[0]
        temp = int(curr.get("temp_C", 0))
        feels = int(curr.get("FeelsLikeC", temp))
        desc_list = curr.get("lang_zh", curr.get("weatherDesc", [{}]))
        desc = desc_list[0].get("value", "") if desc_list else ""
        code = curr.get("weatherCode", "113")
        is_day = int(curr.get("visibility", "10")) > 0  # 粗略判断

        weather_info = {
            "temp": temp,
            "feels_like": feels,
            "description": _wttr_desc_zh(code, desc),
            "icon": _wttr_icon(code, is_day),
            "city": settings.WEATHER_CITY,
        }
        logger.info("wttr.in 天气已获取: %s°C %s", temp, weather_info["description"])
        return weather_info
    except Exception as e:
        logger.error("wttr.in 天气获取失败: %s", e)
        return None


def _get_forecast_from_wttr() -> Optional[list[dict]]:
    """
    wttr.in fallback：未来 3 天预报
    """
    try:
        url = f"https://wttr.in/{settings.WEATHER_CITY}?format=j1"
        resp = requests.get(url, headers={"User-Agent": "mars-sandbox/1.0"}, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        weather_days = data.get("weather", [])
        today_str = date.today().isoformat()
        result = []
        for day in weather_days:
            dt_str = day.get("date", "")
            if dt_str <= today_str:
                continue
            # 取中午时段的天气描述
            hourly = day.get("hourly", [])
            noon = hourly[4] if len(hourly) > 4 else (hourly[0] if hourly else {})
            code = noon.get("weatherCode", "113")
            desc_list = noon.get("lang_zh", noon.get("weatherDesc", [{}]))
            desc = desc_list[0].get("value", "") if desc_list else ""
            result.append({
                "date": dt_str,
                "icon": _wttr_icon(code),
                "temp_max": int(day.get("maxtempC", 0)),
                "temp_min": int(day.get("mintempC", 0)),
                "description": _wttr_desc_zh(code, desc),
            })
            if len(result) >= 3:
                break

        logger.info("wttr.in 预报已获取: %d 天", len(result))
        return result
    except Exception as e:
        logger.error("wttr.in 预报获取失败: %s", e)
        return None


def _get_weather() -> Optional[dict]:
    """
    获取当前天气：优先 OpenWeatherMap，失败则 fallback wttr.in
    缓存 30 分钟
    """
    now = time.time()
    if _weather_cache["data"] and (now - _weather_cache["timestamp"]) < WEATHER_CACHE_TTL:
        return _weather_cache["data"]

    api_key = settings.OPENWEATHERMAP_API_KEY
    if api_key:
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?lat={settings.WEATHER_LAT}&lon={settings.WEATHER_LON}"
                f"&appid={api_key}&units=metric&lang=zh_cn"
            )
            resp = requests.get(url, headers={"User-Agent": "mars-sandbox/1.0"}, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            weather_info = {
                "temp": round(data["main"]["temp"]),
                "feels_like": round(data["main"].get("feels_like", data["main"]["temp"])),
                "description": data["weather"][0]["description"] if data.get("weather") else "",
                "icon": data["weather"][0]["icon"] if data.get("weather") else "01d",
                "city": settings.WEATHER_CITY,
            }
            _weather_cache["data"] = weather_info
            _weather_cache["timestamp"] = now
            logger.info("OpenWeatherMap 天气已更新: %s°C %s", weather_info["temp"], weather_info["description"])
            return weather_info
        except Exception as e:
            logger.warning("OpenWeatherMap 失败，尝试 wttr.in fallback: %s", e)

    # fallback: wttr.in
    result = _get_weather_from_wttr()
    if result:
        _weather_cache["data"] = result
        _weather_cache["timestamp"] = now
    return result or _weather_cache["data"]


def _get_weather_forecast() -> Optional[list[dict]]:
    """
    获取未来 3 天天气预报：优先 OpenWeatherMap，失败则 fallback wttr.in
    缓存 1 小时
    """
    now = time.time()
    if _weather_forecast_cache["data"] and (now - _weather_forecast_cache["timestamp"]) < WEATHER_FORECAST_CACHE_TTL:
        return _weather_forecast_cache["data"]

    api_key = settings.OPENWEATHERMAP_API_KEY
    if api_key:
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/forecast"
                f"?lat={settings.WEATHER_LAT}&lon={settings.WEATHER_LON}"
                f"&appid={api_key}&units=metric&lang=zh_cn"
            )
            resp = requests.get(url, headers={"User-Agent": "mars-sandbox/1.0"}, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            # 按天聚合，取最高/最低温
            daily: dict = {}
            for item in data.get("list", []):
                dt_str = item["dt_txt"].split(" ")[0]  # yyyy-MM-dd
                if dt_str not in daily:
                    daily[dt_str] = {
                        "date": dt_str,
                        "temp_max": item["main"]["temp_max"],
                        "temp_min": item["main"]["temp_min"],
                        "icon": item["weather"][0]["icon"] if item.get("weather") else "01d",
                        "description": item["weather"][0]["description"] if item.get("weather") else "",
                    }
                else:
                    daily[dt_str]["temp_max"] = max(daily[dt_str]["temp_max"], item["main"]["temp_max"])
                    daily[dt_str]["temp_min"] = min(daily[dt_str]["temp_min"], item["main"]["temp_min"])

            # 取未来 3 天（排除今天）
            today_str = date.today().isoformat()
            forecast = [v for k, v in sorted(daily.items()) if k > today_str][:3]
            forecast = [
                {
                    "date": f["date"],
                    "icon": f["icon"],
                    "temp_max": round(f["temp_max"]),
                    "temp_min": round(f["temp_min"]),
                    "description": f["description"],
                }
                for f in forecast
            ]

            _weather_forecast_cache["data"] = forecast
            _weather_forecast_cache["timestamp"] = now
            logger.info("OpenWeatherMap 预报已更新: %d 天", len(forecast))
            return forecast
        except Exception as e:
            logger.warning("OpenWeatherMap 预报失败，尝试 wttr.in fallback: %s", e)

    # fallback: wttr.in
    result = _get_forecast_from_wttr()
    if result:
        _weather_forecast_cache["data"] = result
        _weather_forecast_cache["timestamp"] = now
    return result or _weather_forecast_cache["data"]


def _get_daily_background() -> Optional[str]:
    """
    获取 Bing 每日壁纸 URL，每小时轮转不同图片
    缓存 1 小时
    """
    now = time.time()
    if _background_cache["data"] and (now - _background_cache["timestamp"]) < BACKGROUND_CACHE_TTL:
        return _background_cache["data"]

    try:
        # 获取 8 张壁纸，按小时轮转
        url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt=zh-CN"
        resp = requests.get(url, headers={"User-Agent": "mars-sandbox/1.0"}, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        images = data.get("images")
        if images:
            hour_idx = datetime.now().hour % len(images)
            img = images[hour_idx]
            bg_url = f"https://www.bing.com{img['url']}"
            _background_cache["data"] = bg_url
            _background_cache["timestamp"] = now
            logger.info("Bing 壁纸已更新 (hour=%d): %s", hour_idx, img.get("title", ""))
            return bg_url
    except Exception as e:
        logger.error("获取 Bing 壁纸失败: %s", e)
        return _background_cache["data"]

    return None


def _get_db_dashboard_data(db) -> dict:
    """获取数据库相关的看板数据（同步，本地查询很快）"""
    return {
        "meal_plans": _get_meal_plans(db),
        "recent_meals": _get_recent_meals(db),
        "travel_pages": _get_travel_pages(db),
        "messages": _get_board_messages(db),
        "family_members": _get_family_members(db),
    }


async def build_full_dashboard_data() -> dict:
    """构建完整的看板数据（异步并发获取外部 API，避免阻塞事件循环）"""
    db = SessionLocal()
    try:
        # 数据库查询（同步但很快）
        db_data = _get_db_dashboard_data(db)

        # 外部 API 并发请求（天气、预报、壁纸）
        weather, forecast, bg = await asyncio.gather(
            asyncio.to_thread(_get_weather),
            asyncio.to_thread(_get_weather_forecast),
            asyncio.to_thread(_get_daily_background),
        )

        return {
            **db_data,
            "weather": weather,
            "weather_forecast": forecast,
            "background_image": bg,
        }
    finally:
        db.close()


async def _handle_acknowledge_message(message_id, member_id, ws: WebSocket):
    """
    处理留言已读确认（toggle）：
    - 如果成员未确认，则加入 acknowledged_by 列表
    - 如果成员已确认，则从 acknowledged_by 列表移除（取消确认）
    - 广播给所有 dashboard 连接
    """
    if not message_id or not member_id:
        return

    db = SessionLocal()
    try:
        msg = db.query(BoardMessage).filter(BoardMessage.id == message_id).first()
        if not msg:
            return

        # 解析当前已确认列表
        acknowledged = _parse_acknowledged_by(msg)
        member_id_int = int(member_id)

        # Toggle: 如果已确认则移除，否则添加
        if member_id_int in acknowledged:
            acknowledged.remove(member_id_int)
            logger.info("留言 %d 被成员 %d 取消确认", message_id, member_id_int)
        else:
            acknowledged.append(member_id_int)
            logger.info("留言 %d 被成员 %d 确认", message_id, member_id_int)

        msg.acknowledged_by = json.dumps(acknowledged)
        db.commit()
        db.refresh(msg)

        # 广播给所有 dashboard
        await broadcast_to_dashboards({
            "type": "message_acknowledged",
            "message_id": message_id,
            "member_id": member_id_int,
            "acknowledged_by": acknowledged,
        })
    except Exception as e:
        logger.error("处理留言确认失败: %s", e, exc_info=True)
    finally:
        db.close()


async def handle_dashboard_websocket(websocket: WebSocket):
    """
    处理 dashboard WebSocket 连接
    - 连接时推送全量数据
    - 每 30s 刷新一次数据
    - 响应客户端 ping/pong 心跳
    """
    await websocket.accept()
    await register_dashboard(websocket)

    async def send_full_update():
        data = await build_full_dashboard_data()
        msg = {
            "type": "dashboard_update",
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        await websocket.send_json(msg)

    try:
        # 首次推送全量数据
        await send_full_update()

        # 启动定时刷新任务
        async def periodic_refresh():
            while True:
                await asyncio.sleep(30)
                try:
                    await send_full_update()
                except Exception:
                    break

        refresh_task = asyncio.create_task(periodic_refresh())

        # 主循环：接收客户端消息（心跳 / 手动刷新请求 / 留言确认）
        while True:
            try:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                msg_type = msg.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "refresh":
                    await send_full_update()
                elif msg_type == "acknowledge_message":
                    await _handle_acknowledge_message(
                        msg.get("message_id"),
                        msg.get("member_id"),
                        websocket,
                    )

            except WebSocketDisconnect:
                break
            except RuntimeError as e:
                logger.info("Dashboard WS 连接断开 (RuntimeError): %s", e)
                break
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error("Dashboard WS 处理异常: %s", e, exc_info=True)
                break

        refresh_task.cancel()

    except Exception as e:
        logger.error("Dashboard WS 异常: %s", e, exc_info=True)
    finally:
        await unregister_dashboard(websocket)
