"""Node management router - heartbeat-based node discovery."""
import hmac
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import require_auth
from ..models import Node
from ..schemas import NodeHeartbeatRequest, NodeResponse, NodeListResponse

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


def _verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from X-API-Key header."""
    if not hmac.compare_digest(x_api_key, settings.NODE_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
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
    age = (datetime.utcnow() - node.last_heartbeat_at).total_seconds()
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
    _: None = Depends(_verify_api_key),
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
        node.last_heartbeat_at = datetime.utcnow()
    else:
        node = Node(
            node_id=payload.node_id,
            hostname=payload.hostname,
            ip=payload.ip,
            platform=payload.platform,
            version=payload.version,
            uptime_seconds=payload.uptime_seconds,
            status="online",
            last_heartbeat_at=datetime.utcnow(),
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
    _: None = Depends(_verify_api_key),
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
