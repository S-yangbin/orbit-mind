"""
WebSocket router
处理home-agent和dashboard的WebSocket连接请求
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from urllib.parse import parse_qs, urlparse

from .handlers import handle_websocket_connection
from .dashboard import handle_dashboard_websocket

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/agent/{node_id}")
async def websocket_endpoint(websocket: WebSocket, node_id: str):
    """
    WebSocket端点,供home-agent连接
    
    URL格式: /ws/agent/{node_id}?secret={node_secret}
    """
    # 解析query参数获取secret
    secret = ""
    if websocket.query_params:
        secret = websocket.query_params.get("secret", "")
    
    # 接受WebSocket连接
    await websocket.accept()
    
    logger.info("WebSocket连接请求: node_id=%s", node_id)
    
    try:
        # 处理连接
        await handle_websocket_connection(websocket, node_id, secret)
    except WebSocketDisconnect:
        logger.info("节点 %s WebSocket连接断开", node_id)
    except Exception as e:
        logger.error("节点 %s WebSocket处理异常: %s", node_id, str(e), exc_info=True)
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/dashboard")
async def dashboard_websocket_endpoint(websocket: WebSocket):
    """WebSocket端点,供家庭看板前端连接"""
    try:
        await handle_dashboard_websocket(websocket)
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket连接断开")
    except Exception as e:
        logger.error("Dashboard WebSocket处理异常: %s", str(e), exc_info=True)
        try:
            await websocket.close()
        except:
            pass
