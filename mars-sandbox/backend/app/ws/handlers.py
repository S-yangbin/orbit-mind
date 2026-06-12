"""
WebSocket handler for home-agent connections
处理节点注册、心跳、命令和结果消息
"""

import asyncio
import json
import logging
from typing import Dict, Any
from starlette.websockets import WebSocketDisconnect
from websockets.asyncio.server import ServerConnection

from ..config import settings
from ..database import SessionLocal
from ..models import Node
from ..services.command_result import cache_result
from ..utils.timezone import beijing_now
from .connection_pool import pool

logger = logging.getLogger(__name__)


async def handle_websocket_connection(websocket: ServerConnection, node_id: str, secret: str):
    """
    处理单个home-agent的WebSocket连接
    
    Args:
        websocket: WebSocket连接对象
        node_id: 节点ID
        secret: 节点密钥
    """
    # 验证密钥
    if not secret or secret != settings.NODE_API_KEY:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error_code": "AUTH_FAILED",
            "message": "认证失败: 密钥错误",
            "timestamp": beijing_now().isoformat(),
        }))
        await websocket.close()
        logger.warning("节点 %s 认证失败", node_id)
        return
    
    logger.info("节点 %s WebSocket连接建立", node_id)
    
    try:
        # 等待注册消息
        try:
            message = await asyncio.wait_for(websocket.receive_text(), timeout=10)
            data = json.loads(message)
            
            if data.get("type") != "register":
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error_code": "INVALID_MESSAGE",
                    "message": "第一条消息必须是注册消息",
                    "timestamp": beijing_now().isoformat(),
                }))
                await websocket.close()
                return
            
            # 处理注册
            await _handle_register(websocket, node_id, data)
            
        except asyncio.TimeoutError:
            logger.error("节点 %s 注册超时", node_id)
            await websocket.close()
            return
        except RuntimeError as e:
            logger.warning("节点 %s 注册阶段连接断开: %s", node_id, str(e))
            return
        
        # 注册成功,加入连接池
        await pool.register(node_id, websocket)
        
        # 更新数据库状态
        await asyncio.to_thread(_update_node_status, node_id, "online")
        
        # 主循环:处理消息
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "heartbeat":
                    await _handle_heartbeat(node_id, data)
                elif msg_type == "result":
                    await _handle_result(node_id, data)
                elif msg_type == "error":
                    await _handle_node_error(node_id, data)
                else:
                    logger.warning("节点 %s 发送未知消息类型: %s", node_id, msg_type)
                    
            except WebSocketDisconnect as e:
                logger.info("节点 %s WebSocket断开: code=%s", node_id, e.code)
                break
            except RuntimeError as e:
                # Starlette 在连接已关闭时可能抛出 RuntimeError 而非 WebSocketDisconnect
                logger.info("节点 %s WebSocket连接已断开 (RuntimeError): %s", node_id, str(e))
                break
            except json.JSONDecodeError as e:
                logger.error("节点 %s 消息JSON解析失败: %s", node_id, str(e))
            except Exception as e:
                logger.error("节点 %s 处理消息异常: %s", node_id, str(e), exc_info=True)
    
    except Exception as e:
        logger.error("节点 %s WebSocket连接异常: %s", node_id, str(e), exc_info=True)
    finally:
        # 连接关闭,从连接池移除
        await pool.unregister(node_id)
        await asyncio.to_thread(_update_node_status, node_id, "offline")
        logger.info("节点 %s WebSocket连接关闭", node_id)


async def _handle_register(websocket: ServerConnection, node_id: str, data: Dict[str, Any]):
    """处理节点注册消息"""
    logger.info("处理节点 %s 注册请求", node_id)
    
    # 将注册信息写入数据库
    _update_node_register(node_id, data)
    
    # 发送注册确认
    ack = {
        "type": "register_ack",
        "status": "success",
        "message": "注册成功",
        "server_time": beijing_now().isoformat(),
    }
    await websocket.send_text(json.dumps(ack))


async def _handle_heartbeat(node_id: str, data: Dict[str, Any]):
    """处理心跳消息"""
    await pool.update_heartbeat(node_id)
    # 同步更新数据库中的 last_heartbeat_at，供前端 HTTP API 查询（移到线程池避免阻塞事件循环）
    await asyncio.to_thread(_update_node_heartbeat, node_id)
    # 注意: home-agent 端不要求必须收到 heartbeat_ack


async def _handle_result(node_id: str, data: Dict[str, Any]):
    """处理命令执行结果"""
    request_id = data.get("request_id")
    exit_code = data.get("exit_code")
    
    logger.info(
        "收到节点 %s 的命令结果: request_id=%s, exit_code=%d",
        node_id, request_id, exit_code
    )
    
    # 将结果缓存,供HTTP API查询
    cache_result(request_id, data)


async def _handle_node_error(node_id: str, data: Dict[str, Any]):
    """处理节点错误消息"""
    request_id = data.get("request_id")
    error_code = data.get("error_code")
    message = data.get("message")
    
    logger.error(
        "收到节点 %s 的错误: request_id=%s, error_code=%s, message=%s",
        node_id, request_id, error_code, message
    )


def _update_node_register(node_id: str, data: Dict[str, Any]):
    """将注册信息写入数据库（upsert）"""
    try:
        db = SessionLocal()
        try:
            node = db.query(Node).filter(Node.node_id == node_id).first()
            now = beijing_now()
            if node:
                node.hostname = data.get("hostname", node.hostname)
                node.ip = data.get("ip", node.ip)
                node.platform = data.get("platform", node.platform)
                node.version = data.get("version", node.version)
                node.status = "online"
                node.last_heartbeat_at = now
            else:
                node = Node(
                    node_id=node_id,
                    hostname=data.get("hostname", ""),
                    ip=data.get("ip", ""),
                    platform=data.get("platform", ""),
                    version=data.get("version", "1.0.0"),
                    status="online",
                    last_heartbeat_at=now,
                )
                db.add(node)
            db.commit()
            logger.debug("节点 %s 注册信息已写入数据库", node_id)
        finally:
            db.close()
    except Exception as e:
        logger.error("节点 %s 注册信息写入失败: %s", node_id, e)


def _update_node_heartbeat(node_id: str):
    """更新数据库中节点的 last_heartbeat_at"""
    try:
        db = SessionLocal()
        try:
            node = db.query(Node).filter(Node.node_id == node_id).first()
            if node:
                node.last_heartbeat_at = beijing_now()
                node.status = "online"
                db.commit()
                logger.debug("节点 %s 心跳时间已更新", node_id)
        finally:
            db.close()
    except Exception as e:
        logger.error("更新节点 %s 心跳时间失败: %s", node_id, e)


def _update_node_status(node_id: str, status: str):
    """更新数据库中的节点状态"""
    try:
        db = SessionLocal()
        try:
            node = db.query(Node).filter(Node.node_id == node_id).first()
            if node:
                node.status = status
                if status == "online":
                    node.last_heartbeat_at = beijing_now()
                db.commit()
                logger.debug("节点 %s 状态更新为: %s", node_id, status)
        finally:
            db.close()
    except Exception as e:
        logger.error("更新节点 %s 状态失败: %s", node_id, e)
