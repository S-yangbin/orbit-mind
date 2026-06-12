"""
Command execution router
HTTP API for Hermes to send commands to home-agent nodes via WebSocket
"""

import json
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config import settings
from ..dependencies import verify_node_api_key
from ..ws.connection_pool import pool
from ..utils.timezone import beijing_now
from ..services.command_result import wait_for_result

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/commands", tags=["commands"])


class CommandRequest(BaseModel):
    """命令请求"""
    node_id: str
    command: str
    timeout: int = 30


class CommandResponse(BaseModel):
    """命令响应"""
    request_id: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0


@router.post("", response_model=CommandResponse)
async def execute_command(
    payload: CommandRequest,
    _: None = Depends(verify_node_api_key),
):
    """
    发送命令到指定节点并等待结果
    
    Hermes调用此API,通过WebSocket转发命令到home-agent,同步等待执行结果
    """
    node_id = payload.node_id
    command = payload.command
    timeout = payload.timeout
    
    logger.info("收到命令请求: node_id=%s, command=%s, timeout=%d", node_id, command, timeout)
    
    # 检查节点是否在线
    if not await pool.is_online(node_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"节点 {node_id} 离线或不存在",
        )
    
    # 获取WebSocket连接
    websocket = await pool.get_connection(node_id)
    if not websocket:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"节点 {node_id} 连接不可用",
        )
    
    # 生成request_id
    request_id = str(uuid.uuid4())
    
    # 构建命令消息
    command_msg = {
        "type": "command",
        "request_id": request_id,
        "command": command,
        "timeout": timeout,
        "source": "hermes",
        "created_at": beijing_now().isoformat(),
    }
    
    # 发送命令
    try:
        await websocket.send_text(json.dumps(command_msg))
        logger.info("命令已发送到节点 %s: request_id=%s", node_id, request_id)
    except Exception as e:
        logger.error("发送命令到节点 %s 失败: %s", node_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送命令失败: {e}",
        )
    
    result = await wait_for_result(request_id, timeout)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"命令执行超时({timeout}s)",
        )

    logger.info(
        "命令执行完成: request_id=%s, exit_code=%d, duration=%dms",
        request_id, result.get("exit_code"), result.get("duration_ms")
    )

    return CommandResponse(
        request_id=request_id,
        exit_code=result.get("exit_code", -1),
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        duration_ms=result.get("duration_ms", 0),
    )
