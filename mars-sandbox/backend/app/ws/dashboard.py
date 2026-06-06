"""
Dashboard WebSocket handler
推送家庭看板实时数据（食谱、旅游、留言）到前端
"""

import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from typing import Set

from starlette.websockets import WebSocket, WebSocketDisconnect

from ..database import SessionLocal
from ..models import (
    BoardMessage, Page, MealPlan, MealPlanItem, MealLog, Dish
)

logger = logging.getLogger(__name__)

# 全局 dashboard WebSocket 连接集合
_dashboard_connections: Set[WebSocket] = set()
_lock = asyncio.Lock()


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
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


def _get_meal_plans(db) -> list[dict]:
    """获取本周 + 未来 4 周的食谱"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    end_monday = monday + timedelta(days=28)

    plans = (
        db.query(MealPlan)
        .filter(MealPlan.week_start_date >= monday, MealPlan.week_start_date < end_monday)
        .order_by(MealPlan.week_start_date)
        .all()
    )

    result = []
    for plan in plans:
        items = []
        for item in plan.items:
            dish = item.dish
            items.append({
                "id": item.id,
                "date": item.date.isoformat() if item.date else None,
                "meal_type": item.meal_type,
                "dish": {
                    "id": dish.id,
                    "name": dish.name,
                    "category": dish.category or "",
                },
                "sort_order": item.sort_order,
                "is_manual": item.is_manual,
            })
        result.append({
            "id": plan.id,
            "week_start_date": plan.week_start_date.isoformat() if plan.week_start_date else None,
            "status": plan.status,
            "items": items,
        })
    return result


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
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in pages
    ]


def build_full_dashboard_data() -> dict:
    """构建完整的看板数据"""
    db = SessionLocal()
    try:
        return {
            "meal_plans": _get_meal_plans(db),
            "recent_meals": _get_recent_meals(db),
            "travel_pages": _get_travel_pages(db),
            "messages": _get_board_messages(db),
        }
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
        data = build_full_dashboard_data()
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

        # 主循环：接收客户端消息（心跳 / 手动刷新请求）
        while True:
            try:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                msg_type = msg.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "refresh":
                    await send_full_update()

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
