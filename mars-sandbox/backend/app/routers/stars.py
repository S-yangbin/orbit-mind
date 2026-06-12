"""Star reward CRUD routes."""

from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..dependencies import require_auth
from ..models import StarReward
from ..schemas import StarRewardResponse, StarRewardCreate, StarSummary
from ..utils.timezone import beijing_now
from ..ws.dashboard import broadcast_to_dashboards, build_star_update_data

router = APIRouter(prefix="/api/stars", tags=["stars"])

STARS_PER_YUAN = 3  # 1 star = 3 yuan


@router.get("/summary", response_model=StarSummary)
async def get_star_summary(
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """获取星星汇总：总数、可兑换金额、近期记录"""
    # Total stars (all awarded)
    total_row = db.query(
        func.coalesce(func.sum(StarReward.stars), 0)
    ).scalar()
    total_stars = int(total_row)

    # Unredeemed stars
    unredeemed_row = db.query(
        func.coalesce(func.sum(StarReward.stars), 0)
    ).filter(StarReward.redeemed == 0).scalar()
    unredeemed_stars = int(unredeemed_row)

    # Recent 20 records
    recent = (
        db.query(StarReward)
        .order_by(StarReward.created_at.desc())
        .limit(20)
        .all()
    )

    return StarSummary(
        total_stars=total_stars,
        total_value=total_stars * STARS_PER_YUAN,
        unredeemed_stars=unredeemed_stars,
        unredeemed_value=unredeemed_stars * STARS_PER_YUAN,
        recent_stars=[StarRewardResponse.model_validate(r) for r in recent],
    )


@router.get("", response_model=List[StarRewardResponse])
async def list_stars(
    target_date: Optional[str] = Query(None, alias="date", description="日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """获取星星记录列表，可按日期筛选"""
    q = db.query(StarReward)

    if target_date:
        try:
            d = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")
        q = q.filter(func.date(StarReward.created_at) == d)

    total = q.count()
    items = (
        q.order_by(StarReward.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [StarRewardResponse.model_validate(item) for item in items]


@router.post("", response_model=StarRewardResponse)
async def create_star(
    payload: StarRewardCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """添加星星奖励（父母操作）"""
    if payload.stars < 1 or payload.stars > 10:
        raise HTTPException(status_code=400, detail="星星数量需在 1-10 之间")

    star = StarReward(
        stars=payload.stars,
        awarded_by=payload.awarded_by,
        reason=payload.reason,
        related_schedule_id=payload.related_schedule_id,
    )
    db.add(star)
    db.commit()
    db.refresh(star)

    # Broadcast update to all dashboards
    try:
        data = await build_star_update_data()
        await broadcast_to_dashboards({"type": "star_update", "data": data})
    except Exception:
        pass

    return StarRewardResponse.model_validate(star)


@router.post("/{star_id}/redeem", response_model=StarRewardResponse)
async def redeem_star(
    star_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """兑换星星"""
    star = db.query(StarReward).filter(StarReward.id == star_id).first()
    if not star:
        raise HTTPException(status_code=404, detail="星星记录不存在")

    if star.redeemed == 1:
        raise HTTPException(status_code=400, detail="该星星已兑换过")

    star.redeemed = 1
    star.redeemed_at = beijing_now()
    db.commit()
    db.refresh(star)

    # Broadcast update to all dashboards
    try:
        data = await build_star_update_data()
        await broadcast_to_dashboards({"type": "star_update", "data": data})
    except Exception:
        pass

    return StarRewardResponse.model_validate(star)


@router.delete("/{star_id}")
async def delete_star(
    star_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """删除星星记录（撤回误操作）"""
    star = db.query(StarReward).filter(StarReward.id == star_id).first()
    if not star:
        raise HTTPException(status_code=404, detail="星星记录不存在")

    db.delete(star)
    db.commit()

    # Broadcast update to all dashboards
    try:
        data = await build_star_update_data()
        await broadcast_to_dashboards({"type": "star_update", "data": data})
    except Exception:
        pass

    return {"ok": True}
