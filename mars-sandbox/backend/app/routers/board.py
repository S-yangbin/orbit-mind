"""Board messages CRUD routes."""
import asyncio
import json
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_auth
from ..models import BoardMessage
from ..schemas import BoardMessageCreate, BoardMessageUpdate, BoardMessageResponse, BoardMessageListResponse
from ..ws.dashboard import broadcast_to_dashboards, build_full_dashboard_data

router = APIRouter(prefix="/api/board", tags=["board"])


def _parse_acknowledged_by(msg: BoardMessage) -> Optional[List[int]]:
    """解析 acknowledged_by JSON 字段"""
    if msg.acknowledged_by is None:
        return None
    if isinstance(msg.acknowledged_by, list):
        return msg.acknowledged_by
    try:
        return json.loads(msg.acknowledged_by)
    except (json.JSONDecodeError, TypeError):
        return None


def _msg_to_response(msg: BoardMessage) -> BoardMessageResponse:
    return BoardMessageResponse(
        id=msg.id,
        content=msg.content,
        author=msg.author,
        color=msg.color,
        pinned=msg.pinned,
        expires_at=msg.expires_at,
        acknowledged_by=_parse_acknowledged_by(msg),
        created_at=msg.created_at,
        updated_at=msg.updated_at,
    )


def _msg_to_dict(msg: BoardMessage) -> dict:
    return {
        "id": msg.id,
        "content": msg.content,
        "author": msg.author,
        "color": msg.color,
        "pinned": msg.pinned,
        "expires_at": msg.expires_at.isoformat() if msg.expires_at else None,
        "acknowledged_by": _parse_acknowledged_by(msg) or [],
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


@router.get("/messages", response_model=BoardMessageListResponse)
async def list_messages(
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Get all messages, pinned first, then by created_at desc."""
    messages = (
        db.query(BoardMessage)
        .order_by(BoardMessage.pinned.desc(), BoardMessage.created_at.desc())
        .all()
    )
    return BoardMessageListResponse(items=[_msg_to_response(m) for m in messages])


@router.post("/messages", response_model=BoardMessageResponse)
async def create_message(
    payload: BoardMessageCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Create a new board message."""
    msg = BoardMessage(
        content=payload.content,
        author=payload.author,
        color=payload.color,
        expires_at=payload.expires_at,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # 广播到所有 dashboard
    await broadcast_to_dashboards({
        "type": "message_added",
        "message": _msg_to_dict(msg),
    })

    return _msg_to_response(msg)


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Delete a board message."""
    msg = db.query(BoardMessage).filter(BoardMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()

    # 广播到所有 dashboard
    await broadcast_to_dashboards({
        "type": "message_deleted",
        "message": {"id": message_id},
    })

    return {"status": "ok"}


@router.put("/messages/{message_id}", response_model=BoardMessageResponse)
async def update_message(
    message_id: int,
    payload: BoardMessageUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Update a board message (content, author, color, expires_at)."""
    msg = db.query(BoardMessage).filter(BoardMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if payload.content is not None:
        msg.content = payload.content
    if payload.author is not None:
        msg.author = payload.author
    if payload.color is not None:
        msg.color = payload.color
    if payload.expires_at is not None:
        msg.expires_at = payload.expires_at
    db.commit()
    db.refresh(msg)

    # 广播到所有 dashboard
    await broadcast_to_dashboards({
        "type": "message_updated",
        "message": _msg_to_dict(msg),
    })

    return _msg_to_response(msg)


@router.put("/messages/{message_id}/pin", response_model=BoardMessageResponse)
async def toggle_pin(
    message_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Toggle pinned status of a board message."""
    msg = db.query(BoardMessage).filter(BoardMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.pinned = 0 if msg.pinned else 1
    db.commit()
    db.refresh(msg)

    # 广播到所有 dashboard
    await broadcast_to_dashboards({
        "type": "message_pinned",
        "message": _msg_to_dict(msg),
    })

    return _msg_to_response(msg)
