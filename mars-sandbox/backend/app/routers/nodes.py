"""Node management router - heartbeat-based node discovery."""
import hmac
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import require_auth, verify_node_api_key
from ..models import Node
from ..schemas import NodeHeartbeatRequest, NodeResponse, NodeListResponse
from ..utils.timezone import beijing_now
from ..ws.connection_pool import pool
from ..services.command_result import wait_for_result

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


def _verify_api_key_or_cookie(request: Request, x_api_key: Optional[str] = Header(None)):
    """Verify either API key header or session cookie."""
    # Check API key first
    if x_api_key and hmac.compare_digest(x_api_key, settings.NODE_API_KEY):
        return
    # Fall back to cookie auth
    from ..auth import get_current_user
    user = get_current_user(request)
    if user:
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def _format_uptime(seconds: int) -> str:
    """Format uptime seconds to human-readable string."""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "just started"


def _compute_status(node: Node, stale_seconds: int) -> str:
    """Compute real-time status based on last_heartbeat_at."""
    if not node.last_heartbeat_at:
        return "offline"
    now = beijing_now()
    last = node.last_heartbeat_at
    # 数据库读出可能是 naive datetime，统一去掉 tzinfo 再比较
    if last.tzinfo is None and now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    elif last.tzinfo is not None and now.tzinfo is None:
        last = last.replace(tzinfo=None)
    age = (now - last).total_seconds()
    return "online" if age <= stale_seconds else "offline"


def _node_to_response(node: Node, stale_seconds: int) -> NodeResponse:
    """Convert Node ORM object to NodeResponse schema."""
    real_status = _compute_status(node, stale_seconds)
    return NodeResponse(
        node_id=node.node_id,
        hostname=node.hostname or "",
        ip=node.ip or "",
        platform=node.platform or "",
        version=node.version or "1.0.0",
        status=real_status,
        last_heartbeat_at=node.last_heartbeat_at,
        uptime_seconds=node.uptime_seconds or 0,
        uptime=_format_uptime(node.uptime_seconds or 0),
    )


@router.put("/heartbeat")
async def heartbeat(
    payload: NodeHeartbeatRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_node_api_key),
):
    """Upsert node heartbeat. Called by home-agent periodically."""
    node = db.query(Node).filter(Node.node_id == payload.node_id).first()

    if node:
        node.hostname = payload.hostname
        node.ip = payload.ip
        node.platform = payload.platform
        node.version = payload.version
        node.uptime_seconds = payload.uptime_seconds
        node.status = "online"
        node.last_heartbeat_at = beijing_now()
    else:
        node = Node(
            node_id=payload.node_id,
            hostname=payload.hostname,
            ip=payload.ip,
            platform=payload.platform,
            version=payload.version,
            uptime_seconds=payload.uptime_seconds,
            status="online",
            last_heartbeat_at=beijing_now(),
        )
        db.add(node)

    db.commit()
    db.refresh(node)

    return {
        "status": "ok",
        "node_id": node.node_id,
        "message": "Heartbeat recorded",
    }


@router.get("", response_model=NodeListResponse)
async def list_nodes(
    stale: int = 180,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_api_key_or_cookie),
):
    """List all registered nodes with real-time online/offline status."""
    nodes: List[Node] = db.query(Node).order_by(Node.node_id).all()

    stale_seconds = max(stale, 30)  # minimum 30s
    result = []
    for node in nodes:
        resp = _node_to_response(node, stale_seconds)
        result.append(resp)

    # Sort: online first, then by node_id
    result.sort(key=lambda n: (0 if n.status == "online" else 1, n.node_id))

    return NodeListResponse(
        total=len(result),
        online=len([n for n in result if n.status == "online"]),
        offline=len([n for n in result if n.status == "offline"]),
        nodes=result,
    )


class NodeCommandRequest(BaseModel):
    """Dashboard 命令请求"""
    command: str
    timeout: int = 30


class NodeCommandResponse(BaseModel):
    """Dashboard 命令响应"""
    request_id: str
    node_id: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0


@router.post("/{node_id}/command", response_model=NodeCommandResponse)
async def execute_node_command(
    node_id: str,
    payload: NodeCommandRequest,
    _=Depends(require_auth),
):
    """Dashboard 发送命令到指定节点并等待结果（cookie 认证）"""
    command = payload.command
    timeout = payload.timeout

    logger.info("Dashboard 命令请求: node_id=%s, command=%s", node_id, command)

    if not await pool.is_online(node_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"节点 {node_id} 离线或不存在",
        )

    websocket = await pool.get_connection(node_id)
    if not websocket:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"节点 {node_id} 连接不可用",
        )

    request_id = str(uuid.uuid4())
    command_msg = {
        "type": "command",
        "request_id": request_id,
        "command": command,
        "timeout": timeout,
        "source": "dashboard",
        "created_at": beijing_now().isoformat(),
    }

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
        "Dashboard 命令执行完成: node_id=%s, request_id=%s, exit_code=%d",
        node_id, request_id, result.get("exit_code", -1),
    )

    return NodeCommandResponse(
        request_id=request_id,
        node_id=node_id,
        exit_code=result.get("exit_code", -1),
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        duration_ms=result.get("duration_ms", 0),
    )


@router.delete("/{node_id}")
async def delete_node(
    node_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Delete a node (requires cookie auth, for Dashboard management)."""
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    db.delete(node)
    db.commit()

    return {"status": "ok", "message": f"Node '{node_id}' deleted"}
