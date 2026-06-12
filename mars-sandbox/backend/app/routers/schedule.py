"""Learning plan (children's daily schedule) CRUD routes."""

import asyncio
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..dependencies import require_auth
from ..models import ActivityType, WeeklyTemplate, WeeklyTemplateDay, DailySchedule
from ..schemas import (
    ActivityTypeResponse, ActivityTypeCreate, ActivityTypeUpdate,
    WeeklyTemplateResponse, WeeklyTemplateCreate, WeeklyTemplateDayItem,
    DailyScheduleResponse, DailyScheduleCreate, DailyScheduleUpdate,
)
from ..utils.timezone import beijing_now
from ..ws.dashboard import broadcast_to_dashboards, build_full_dashboard_data

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


# ─────────────────────────────────────────────────────────────────────────────
# Activity Types
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/activity-types", response_model=List[ActivityTypeResponse])
async def list_activity_types(
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """获取所有活动类型"""
    types = db.query(ActivityType).order_by(ActivityType.sort_order, ActivityType.id).all()
    return [ActivityTypeResponse.model_validate(t) for t in types]


@router.post("/activity-types", response_model=ActivityTypeResponse)
async def create_activity_type(
    payload: ActivityTypeCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """创建自定义活动类型"""
    # 检查名称唯一性
    existing = db.query(ActivityType).filter(ActivityType.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"活动类型 '{payload.name}' 已存在")

    max_order = db.query(ActivityType).count()
    at = ActivityType(
        name=payload.name,
        icon=payload.icon,
        category=payload.category,
        color=payload.color,
        is_preset=0,
        sort_order=max_order,
    )
    db.add(at)
    db.commit()
    db.refresh(at)
    return ActivityTypeResponse.model_validate(at)


@router.put("/activity-types/{type_id}", response_model=ActivityTypeResponse)
async def update_activity_type(
    type_id: int,
    payload: ActivityTypeUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """更新活动类型"""
    at = db.query(ActivityType).filter(ActivityType.id == type_id).first()
    if not at:
        raise HTTPException(status_code=404, detail="活动类型不存在")

    if payload.name is not None:
        dup = db.query(ActivityType).filter(ActivityType.name == payload.name, ActivityType.id != type_id).first()
        if dup:
            raise HTTPException(status_code=400, detail=f"活动类型 '{payload.name}' 已存在")
        at.name = payload.name
    if payload.icon is not None:
        at.icon = payload.icon
    if payload.category is not None:
        at.category = payload.category
    if payload.color is not None:
        at.color = payload.color
    if payload.sort_order is not None:
        at.sort_order = payload.sort_order

    db.commit()
    db.refresh(at)
    return ActivityTypeResponse.model_validate(at)


@router.delete("/activity-types/{type_id}")
async def delete_activity_type(
    type_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """删除活动类型"""
    at = db.query(ActivityType).filter(ActivityType.id == type_id).first()
    if not at:
        raise HTTPException(status_code=404, detail="活动类型不存在")

    db.delete(at)
    db.commit()
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
# Weekly Template
# ─────────────────────────────────────────────────────────────────────────────

def _template_to_response(tpl: WeeklyTemplate) -> WeeklyTemplateResponse:
    days = [
        WeeklyTemplateDayItem(
            day_of_week=d.day_of_week,
            activity_type_id=d.activity_type_id,
            sort_order=d.sort_order,
        )
        for d in tpl.days
    ]
    return WeeklyTemplateResponse(
        id=tpl.id,
        name=tpl.name,
        child_id=tpl.child_id,
        is_active=tpl.is_active,
        days=days,
        created_at=tpl.created_at,
        updated_at=tpl.updated_at,
    )


@router.get("/template", response_model=Optional[WeeklyTemplateResponse])
async def get_active_template(
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """获取当前激活的周模板"""
    tpl = (
        db.query(WeeklyTemplate)
        .options(joinedload(WeeklyTemplate.days))
        .filter(WeeklyTemplate.is_active == 1)
        .first()
    )
    if not tpl:
        return None
    return _template_to_response(tpl)


@router.post("/template", response_model=WeeklyTemplateResponse)
async def create_or_update_template(
    payload: WeeklyTemplateCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """创建或更新周模板（替换当前激活的模板）"""
    # 将现有激活模板标记为非激活
    db.query(WeeklyTemplate).filter(WeeklyTemplate.is_active == 1).update({"is_active": 0})

    tpl = WeeklyTemplate(name=payload.name, is_active=1)
    db.add(tpl)
    db.flush()  # 获取 tpl.id

    for day_item in payload.days:
        if not (0 <= day_item.day_of_week <= 6):
            raise HTTPException(status_code=400, detail=f"day_of_week 必须在 0-6 之间，收到 {day_item.day_of_week}")
        day = WeeklyTemplateDay(
            template_id=tpl.id,
            day_of_week=day_item.day_of_week,
            activity_type_id=day_item.activity_type_id,
            sort_order=day_item.sort_order,
        )
        db.add(day)

    db.commit()
    db.refresh(tpl)
    # 重新加载 days 关系
    db.refresh(tpl, ["days"])
    return _template_to_response(tpl)


# ─────────────────────────────────────────────────────────────────────────────
# Daily Schedule
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_daily_from_template(db: Session, target_date: date) -> None:
    """如果 target_date 无记录，则从周模板自动生成当天活动列表"""
    existing = db.query(DailySchedule).filter(DailySchedule.date == target_date).first()
    if existing is not None:
        return  # 已有记录，不覆盖

    # 查找激活的模板
    tpl = (
        db.query(WeeklyTemplate)
        .options(joinedload(WeeklyTemplate.days))
        .filter(WeeklyTemplate.is_active == 1)
        .first()
    )
    if not tpl:
        return  # 无模板，跳过

    # 0=Monday ... 6=Sunday
    dow = target_date.weekday()
    template_days = [d for d in tpl.days if d.day_of_week == dow]
    if not template_days:
        return  # 当天模板为空

    for td in template_days:
        item = DailySchedule(
            date=target_date,
            activity_type_id=td.activity_type_id,
            sort_order=td.sort_order,
            is_override=0,
        )
        db.add(item)
    db.commit()


@router.get("/daily", response_model=List[DailyScheduleResponse])
async def get_daily_schedule(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """获取某天的计划（自动从模板生成）"""
    if target_date is None:
        target_date = date.today()

    _ensure_daily_from_template(db, target_date)

    items = (
        db.query(DailySchedule)
        .options(joinedload(DailySchedule.activity_type))
        .filter(DailySchedule.date == target_date)
        .order_by(DailySchedule.sort_order, DailySchedule.id)
        .all()
    )
    return [DailyScheduleResponse.model_validate(i) for i in items]


@router.get("/daily/range", response_model=List[DailyScheduleResponse])
async def get_daily_range(
    start: date,
    end: date,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """获取日期范围内的计划"""
    if start > end:
        raise HTTPException(status_code=400, detail="start 日期不能晚于 end 日期")

    from datetime import timedelta
    current = start
    while current <= end:
        _ensure_daily_from_template(db, current)
        current += timedelta(days=1)

    items = (
        db.query(DailySchedule)
        .options(joinedload(DailySchedule.activity_type))
        .filter(DailySchedule.date >= start, DailySchedule.date <= end)
        .order_by(DailySchedule.date, DailySchedule.sort_order, DailySchedule.id)
        .all()
    )
    return [DailyScheduleResponse.model_validate(i) for i in items]


@router.post("/daily", response_model=DailyScheduleResponse)
async def add_daily_item(
    payload: DailyScheduleCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """手动添加活动到某天"""
    # 确保活动类型存在
    at = db.query(ActivityType).filter(ActivityType.id == payload.activity_type_id).first()
    if not at:
        raise HTTPException(status_code=404, detail="活动类型不存在")

    item = DailySchedule(
        date=payload.date,
        activity_type_id=payload.activity_type_id,
        sort_order=payload.sort_order,
        is_override=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    db.refresh(item, ["activity_type"])

    # 广播更新到所有 dashboard
    try:
        data = await build_full_dashboard_data()
        await broadcast_to_dashboards({"type": "dashboard_update", "data": data})
    except Exception:
        pass

    return DailyScheduleResponse.model_validate(item)


@router.put("/daily/{item_id}", response_model=DailyScheduleResponse)
async def update_daily_item(
    item_id: int,
    payload: DailyScheduleUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """更新活动状态（标记完成/未完成 + 完成备注）"""
    item = db.query(DailySchedule).filter(DailySchedule.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动记录不存在")

    if payload.completed is not None:
        item.completed = payload.completed
        item.completed_at = beijing_now() if payload.completed == 1 else None
    if payload.completion_note is not None:
        item.completion_note = payload.completion_note

    db.commit()
    db.refresh(item)
    db.refresh(item, ["activity_type"])

    # 广播更新到所有 dashboard
    try:
        data = await build_full_dashboard_data()
        await broadcast_to_dashboards({"type": "dashboard_update", "data": data})
    except Exception:
        pass

    return DailyScheduleResponse.model_validate(item)


@router.delete("/daily/{item_id}")
async def delete_daily_item(
    item_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """删除某天的某个活动"""
    item = db.query(DailySchedule).filter(DailySchedule.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="活动记录不存在")

    db.delete(item)
    db.commit()

    # 广播更新到所有 dashboard
    try:
        data = await build_full_dashboard_data()
        await broadcast_to_dashboards({"type": "dashboard_update", "data": data})
    except Exception:
        pass

    return {"ok": True}
