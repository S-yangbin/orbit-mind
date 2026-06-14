"""Meal planning and dish recognition router."""
import io
import json
import logging
import os
import uuid
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from PIL import Image as PILImage, ImageOps as PILImageOps

from ..config import settings
from ..database import get_db
from ..dependencies import require_auth
from ..models import FamilyMember, Dish, MealPlan, MealPlanItem, MealLog, DishPreference
from ..utils.json_helpers import parse_json_field
from ..utils.timezone import beijing_now
from ..schemas import (
    FamilyMemberResponse, FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberListResponse,
    DishResponse, DishCreate, DishUpdate, DishListResponse,
    MealPlanResponse, MealPlanCurrentResponse, MealPlanGenerateRequest,
    MealPlanItemResponse, MealPlanItemAdd, MealPlanItemReplace, MealPlanItemDish,
    PhotoRecognizeResponse, RecognizedDish,
    MealLogCreate, MealLogResponse, MealLogListResponse, MealLogDishOutput,
    MealHistoryStatsResponse, DishPreferenceResponse, MemberPreferenceSummary, DishLikedByResponse,
)
from ..services.ai_service import recognize_dishes, generate_monthly_weekend_plan, AIGenerationError
from ..ws.dashboard import broadcast_to_dashboards, _get_meal_plans

logger = logging.getLogger(__name__)


async def _broadcast_meal_plan_update(db: Session):
    """菜单变更后，重新查询菜单数据并广播到所有 Dashboard"""
    try:
        meal_plans = _get_meal_plans(db)
        await broadcast_to_dashboards({
            "type": "meal_plan_updated",
            "data": {"meal_plans": meal_plans},
        })
        logger.info("菜单变更已广播到 Dashboard")
    except Exception as e:
        logger.error("广播菜单更新失败: %s", e, exc_info=True)


router = APIRouter(prefix="/api/meals", tags=["meals"])


# ============================================================
# Helpers
# ============================================================

def _normalize_liked_by(value) -> dict:
    """Normalize liked_by field: old format is List[int], new format is Dict[str, List[int]]."""
    parsed = parse_json_field(value)
    if isinstance(parsed, dict):
        return parsed
    # Old format was a flat list of member IDs — can't map to per-dish, return empty
    return {}


def _dish_to_response(dish: Dish) -> DishResponse:
    return DishResponse(
        id=dish.id,
        name=dish.name,
        category=dish.category,
        ingredients=parse_json_field(dish.ingredients) or [],
        recipe=dish.recipe,
        tags=parse_json_field(dish.tags) or [],
        origin=dish.origin,
        photo_count=dish.photo_count,
        created_at=dish.created_at,
    )


def _member_to_response(m: FamilyMember, db: Session = None) -> FamilyMemberResponse:
    liked_dishes = []
    if db:
        prefs = db.query(DishPreference).filter(DishPreference.member_id == m.id) \
            .order_by(DishPreference.like_count.desc()).limit(20).all()
        for p in prefs:
            dish = db.query(Dish).filter(Dish.id == p.dish_id).first()
            if dish:
                liked_dishes.append({
                    "dish_id": p.dish_id,
                    "dish_name": dish.name,
                    "like_count": p.like_count,
                    "last_liked_at": p.last_liked_at,
                })
    return FamilyMemberResponse(
        id=m.id,
        name=m.name,
        role=m.role,
        avatar=m.avatar,
        preferences=parse_json_field(m.preferences),
        allergies=parse_json_field(m.allergies),
        board_color=m.board_color,
        liked_dishes=liked_dishes if liked_dishes else None,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _plan_item_to_response(item: MealPlanItem, source: Optional[str] = None) -> MealPlanItemResponse:
    dish = item.dish
    return MealPlanItemResponse(
        id=item.id,
        date=item.date,
        meal_type=item.meal_type,
        dish=MealPlanItemDish(
            id=dish.id,
            name=dish.name,
            category=dish.category,
            ingredients=parse_json_field(dish.ingredients) or [],
            recipe=dish.recipe,
        ),
        sort_order=item.sort_order,
        is_manual=item.is_manual,
        source=source,
    )


def _get_or_create_dish(db: Session, name: str, category: str = "荤菜", origin: str = "ai", recipe: str = "") -> Dish:
    """Find dish by name or create it. Handles race conditions."""
    name = name.strip()
    dish = db.query(Dish).filter(Dish.name == name).first()
    if dish:
        return dish
    dish = Dish(name=name, category=category, origin=origin, recipe=recipe or None)
    db.add(dish)
    try:
        db.flush()
    except Exception:
        db.rollback()
        # Race condition: another request created the dish
        dish = db.query(Dish).filter(Dish.name == name).first()
        if dish:
            return dish
        raise
    return dish


def _get_current_week_start() -> date:
    """Get Monday of the current week."""
    today = date.today()
    return today - timedelta(days=today.weekday())


def _infer_meal_type() -> str:
    """Infer meal type from current time."""
    hour = datetime.now().hour
    if hour < 10:
        return "breakfast"
    elif hour < 15:
        return "lunch"
    return "dinner"


def _seed_default_members(db: Session):
    """Insert default 4 family members if table is empty."""
    count = db.query(FamilyMember).count()
    if count > 0:
        return
    defaults = [
        FamilyMember(name="爸爸", role="father", avatar="\U0001f468",
                     preferences=json.dumps({"likes": [], "dislikes": [], "note": ""}),
                     allergies=json.dumps([])),
        FamilyMember(name="妈妈", role="mother", avatar="\U0001f469",
                     preferences=json.dumps({"likes": [], "dislikes": [], "note": ""}),
                     allergies=json.dumps([])),
        FamilyMember(name="孩子", role="child", avatar="\U0001f467",
                     preferences=json.dumps({"likes": [], "dislikes": [], "note": ""}),
                     allergies=json.dumps([])),
        FamilyMember(name="奶奶", role="grandma", avatar="\U0001f475",
                     preferences=json.dumps({"likes": [], "dislikes": [], "note": ""}),
                     allergies=json.dumps([])),
    ]
    db.add_all(defaults)
    db.commit()


# ============================================================
# Family Members
# ============================================================

@router.get("/members", response_model=FamilyMemberListResponse)
async def list_members(
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    _seed_default_members(db)
    members = db.query(FamilyMember).order_by(FamilyMember.id).all()
    return FamilyMemberListResponse(members=[_member_to_response(m, db) for m in members])


@router.post("/members", response_model=FamilyMemberResponse)
async def create_member(
    payload: FamilyMemberCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Create a new family member."""
    # Generate unique role using timestamp
    import time
    role = f"custom_{int(time.time())}"
    member = FamilyMember(
        name=payload.name,
        role=role,
        avatar=payload.avatar,
        board_color=payload.board_color,
        preferences=json.dumps({"likes": [], "dislikes": [], "note": ""}),
        allergies=json.dumps([]),
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _member_to_response(member, db)


@router.delete("/members/{member_id}")
async def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Delete a family member."""
    member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    # Also delete associated dish preferences
    db.query(DishPreference).filter(DishPreference.member_id == member_id).delete()
    db.delete(member)
    db.commit()
    return {"status": "ok"}


@router.put("/members/{member_id}", response_model=FamilyMemberResponse)
async def update_member(
    member_id: int,
    payload: FamilyMemberUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if payload.name is not None:
        member.name = payload.name
    if payload.avatar is not None:
        member.avatar = payload.avatar
    if payload.preferences is not None:
        member.preferences = json.dumps(payload.preferences, ensure_ascii=False)
    if payload.allergies is not None:
        member.allergies = json.dumps(payload.allergies, ensure_ascii=False)
    if payload.board_color is not None:
        member.board_color = payload.board_color

    db.commit()
    db.refresh(member)
    return _member_to_response(member, db)


# ============================================================
# Dishes
# ============================================================

@router.get("/dishes", response_model=DishListResponse)
async def list_dishes(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    query = db.query(Dish)
    if keyword:
        query = query.filter(Dish.name.contains(keyword))
    if category:
        query = query.filter(Dish.category == category)

    total = query.count()
    items = query.order_by(Dish.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return DishListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_dish_to_response(d) for d in items],
    )


@router.post("/dishes", response_model=DishResponse)
async def create_dish(
    payload: DishCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    existing = db.query(Dish).filter(Dish.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Dish '{payload.name}' already exists")

    dish = Dish(
        name=payload.name,
        category=payload.category,
        ingredients=json.dumps(payload.ingredients or [], ensure_ascii=False),
        recipe=payload.recipe,
        tags=json.dumps(payload.tags or [], ensure_ascii=False),
        origin="manual",
    )
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return _dish_to_response(dish)


@router.get("/dishes/{dish_id}", response_model=DishResponse)
async def get_dish(
    dish_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    return _dish_to_response(dish)


@router.put("/dishes/{dish_id}", response_model=DishResponse)
async def update_dish(
    dish_id: int,
    payload: DishUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    if payload.name is not None and payload.name != dish.name:
        conflict = db.query(Dish).filter(Dish.name == payload.name, Dish.id != dish_id).first()
        if conflict:
            raise HTTPException(status_code=409, detail=f"Dish '{payload.name}' already exists")
        dish.name = payload.name

    if payload.category is not None:
        dish.category = payload.category
    if payload.recipe is not None:
        dish.recipe = payload.recipe
    if payload.tags is not None:
        dish.tags = json.dumps(payload.tags, ensure_ascii=False)

    db.commit()
    db.refresh(dish)
    return _dish_to_response(dish)


@router.delete("/dishes/{dish_id}")
async def delete_dish(
    dish_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    # Cascade: remove all plan items referencing this dish, then delete the dish
    ref_items = db.query(MealPlanItem).filter(MealPlanItem.dish_id == dish_id).all()
    for item in ref_items:
        db.delete(item)

    db.delete(dish)
    db.commit()
    await _broadcast_meal_plan_update(db)
    return {"status": "ok", "removed_plan_items": len(ref_items)}


# ============================================================
# Meal Plan
# ============================================================

@router.get("/plan/current")
async def get_current_plan(
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Return plans for past 4 weeks + next 4 weeks, with meal_log data for past dates."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    # Start from 4 weeks ago, end 4 weeks from now
    start_monday = monday - timedelta(days=28)
    end_monday = monday + timedelta(days=28)

    # Fetch all plans in the range
    plans = (
        db.query(MealPlan)
        .filter(MealPlan.week_start_date >= start_monday, MealPlan.week_start_date < end_monday)
        .order_by(MealPlan.week_start_date)
        .all()
    )

    # Fetch meal logs for the past month (up to today)
    four_weeks_ago = today - timedelta(days=28)
    meal_logs = (
        db.query(MealLog)
        .filter(MealLog.date >= four_weeks_ago, MealLog.date <= today)
        .order_by(MealLog.date)
        .all()
    )

    # Build meal_log lookup: date -> {meal_type -> dishes}
    log_lookup: dict = {}
    log_date_dish_names: dict = {}  # date -> set of dish names
    log_date_photos: dict = {}  # date -> latest image_path
    for log in meal_logs:
        log_date = log.date
        if log_date not in log_lookup:
            log_lookup[log_date] = {}
            log_date_dish_names[log_date] = set()
        log_lookup[log_date].setdefault(log.meal_type, []).append(log)
        dishes = parse_json_field(log.dishes_json) or []
        for d in dishes:
            if isinstance(d, dict) and "name" in d:
                log_date_dish_names[log_date].add(d["name"])
        # Track the latest photo per date
        if log.image_path:
            log_date_photos[log_date] = log.image_path

    result = []
    # Track which (date, meal_type) slots we've processed (to avoid duplicates)
    processed_slots = set()

    # Process plans
    for plan in plans:
        weekend_items = []
        for item in plan.items:
            if item.date.weekday() not in (5, 6):
                continue
            # For past dates with logs, skip plan items (will show logs instead)
            if item.date < today and item.date in log_lookup:
                processed_slots.add((item.date, item.meal_type))
                continue
            # Determine source
            source = None
            if item.date == today and item.date in log_lookup:
                source = "log"
            elif plan.status == "confirmed":
                source = "plan"
            resp_item = _plan_item_to_response(item, source=source)
            weekend_items.append(resp_item)
            processed_slots.add((item.date, item.meal_type))

        if weekend_items:
            result.append({
                "id": plan.id,
                "week_start_date": plan.week_start_date,
                "status": plan.status,
                "items": weekend_items,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
            })

    # Add synthetic entries for ALL past dates with logs (show actual data)
    synthetic_by_week: dict = {}  # week_start_date -> list of items
    for log_date, meal_types in log_lookup.items():
        for meal_type, logs in meal_types.items():
            # Collect unique dishes from all logs for this date/meal_type
            seen_dish_ids = set()
            dish_idx = 0
            for log in logs:
                dishes = parse_json_field(log.dishes_json) or []
                for d in dishes:
                    if not isinstance(d, dict) or "name" not in d:
                        continue
                    # Find dish
                    dish_id = d.get("dish_id")
                    dish_obj = None
                    if dish_id:
                        dish_obj = db.query(Dish).filter(Dish.id == dish_id).first()
                    if not dish_obj:
                        dish_obj = db.query(Dish).filter(Dish.name == d["name"]).first()
                    if not dish_obj or dish_obj.id in seen_dish_ids:
                        continue
                    seen_dish_ids.add(dish_obj.id)
                    resp_item = MealPlanItemResponse(
                        id=-log.id * 100 - dish_idx,
                        date=log_date,
                        meal_type=meal_type,
                        dish=MealPlanItemDish(
                            id=dish_obj.id,
                            name=dish_obj.name,
                            category=dish_obj.category or "其他",
                            ingredients=[],
                            recipe=dish_obj.recipe,
                        ),
                        sort_order=dish_idx,
                        is_manual=0,
                        source="log",
                    )
                    synthetic_by_week.setdefault(
                        log_date - timedelta(days=log_date.weekday()), []
                    ).append(resp_item)
                    dish_idx += 1

    # Merge synthetic log entries into existing plans or create new entries
    for week_start, items in synthetic_by_week.items():
        existing = next((r for r in result if r["week_start_date"] == week_start), None)
        if existing:
            # Filter out any plan items for the same date/meal_type as logs
            log_date_types = {(item.date, item.meal_type) for item in items}
            existing["items"] = [
                i for i in existing["items"]
                if (i.date, i.meal_type) not in log_date_types
            ]
            existing["items"].extend(items)
        else:
            result.append({
                "id": -week_start.toordinal(),
                "week_start_date": week_start,
                "status": "log",
                "items": items,
                "created_at": None,
                "updated_at": None,
            })

    # Sort by week_start_date
    result.sort(key=lambda x: x["week_start_date"] if isinstance(x["week_start_date"], date) else date.fromisoformat(str(x["week_start_date"])))
    # Convert log_date_photos keys to string for JSON
    photos_map = {d.isoformat(): p for d, p in log_date_photos.items()}
    return {"plans": result, "date_photos": photos_map}


@router.post("/plan/generate", response_model=MealPlanResponse)
async def generate_plan(
    payload: MealPlanGenerateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    # Start from today, generate 4 weeks of weekends
    today = date.today()
    start_date = payload.week_start_date or today

    # Collect members
    _seed_default_members(db)
    members = db.query(FamilyMember).order_by(FamilyMember.id).all()
    member_data = []
    for m in members:
        preferences = parse_json_field(m.preferences) or {}
        # Merge dynamically liked dishes into likes
        liked_dishes = db.query(DishPreference).filter(
            DishPreference.member_id == m.id
        ).order_by(DishPreference.like_count.desc()).limit(10).all()
        if liked_dishes:
            existing_likes = set(preferences.get("likes", []))
            for liked in liked_dishes:
                dish = db.query(Dish).filter(Dish.id == liked.dish_id).first()
                if dish and dish.name not in existing_likes:
                    preferences.setdefault("likes", []).append(dish.name)
        member_data.append({
            "name": m.name,
            "role": m.role,
            "preferences": preferences,
            "allergies": parse_json_field(m.allergies) or [],
        })

    # Collect recent dishes (last 4 weeks)
    four_weeks_ago = date.today() - timedelta(days=28)
    recent_logs = db.query(MealLog).filter(MealLog.date >= four_weeks_ago).all()
    recent_dish_names = set()
    for log in recent_logs:
        dishes = parse_json_field(log.dishes_json) or []
        for d in dishes:
            if isinstance(d, dict) and "name" in d:
                recent_dish_names.add(d["name"])

    # Call AI for monthly weekend plan
    try:
        plan_data = generate_monthly_weekend_plan(member_data, list(recent_dish_names), start_date)
    except AIGenerationError as e:
        logger.error("AI菜单生成失败: %s", e)
        raise HTTPException(status_code=502, detail=str(e))
    if not plan_data:
        raise HTTPException(status_code=502, detail="AI生成菜单返回空结果，请稍后重试")

    # Phase 1: Pre-create/find all dishes and commit to get IDs
    all_dishes = {}  # name -> Dish object
    for day_entry in plan_data.get("days", []):
        for meal_type in ["lunch"]:
            for dish_info in day_entry.get("meals", {}).get(meal_type, []):
                name = dish_info.get("name", "").strip()
                if name and name not in all_dishes:
                    category = dish_info.get("category", "荤菜")
                    recipe = dish_info.get("recipe", "")
                    all_dishes[name] = _get_or_create_dish(db, name, category, origin="ai", recipe=recipe)
    db.commit()
    for d in all_dishes.values():
        db.refresh(d)

    # Phase 2: Create plans and items
    plans_by_week = {}  # week_start_date -> plan object
    seen_dish_ids = {}  # (plan_id, date, meal_type) -> set of dish_ids (dedup)
    for day_entry in plan_data.get("days", []):
        day_date_str = day_entry.get("date")
        try:
            day_date = date.fromisoformat(day_date_str) if isinstance(day_date_str, str) else day_date_str
        except (ValueError, TypeError):
            continue

        # Find Monday of this day's week
        monday = day_date - timedelta(days=day_date.weekday())
        if monday not in plans_by_week:
            plan_obj = db.query(MealPlan).filter(MealPlan.week_start_date == monday).first()
            if plan_obj and plan_obj.status == "confirmed":
                plans_by_week[monday] = None
                continue
            if plan_obj:
                # Delete existing AI items from draft plan
                db.query(MealPlanItem).filter(
                    MealPlanItem.meal_plan_id == plan_obj.id,
                    MealPlanItem.is_manual == 0,
                ).delete(synchronize_session=False)
            else:
                plan_obj = MealPlan(week_start_date=monday, status="draft")
                db.add(plan_obj)
            db.flush()
            plans_by_week[monday] = plan_obj

        plan_obj = plans_by_week[monday]
        if plan_obj is None:
            continue
        meals = day_entry.get("meals", {})
        for meal_type in ["lunch"]:
            dish_list = meals.get(meal_type, [])
            slot_key = (plan_obj.id, day_date, meal_type)
            if slot_key not in seen_dish_ids:
                seen_dish_ids[slot_key] = set()
            sort_idx = 0
            for dish_info in dish_list:
                name = dish_info.get("name", "").strip()
                if not name:
                    continue
                dish = all_dishes.get(name)
                if not dish or not dish.id:
                    continue
                if dish.id in seen_dish_ids[slot_key]:
                    continue  # skip duplicate dish in same slot
                seen_dish_ids[slot_key].add(dish.id)
                item = MealPlanItem(
                    meal_plan_id=plan_obj.id,
                    date=day_date,
                    meal_type=meal_type,
                    dish_id=dish.id,
                    sort_order=sort_idx,
                    is_manual=0,
                )
                db.add(item)
                sort_idx += 1

    db.commit()

    # 广播菜单更新到 Dashboard
    await _broadcast_meal_plan_update(db)

    # Return the first week's plan
    first_monday = start_date - timedelta(days=start_date.weekday())
    first_plan = plans_by_week.get(first_monday)
    if not first_plan:
        # Fallback: return first plan created
        first_plan = list(plans_by_week.values())[0] if plans_by_week else None
    if not first_plan:
        raise HTTPException(status_code=502, detail="No plan created")

    items = [_plan_item_to_response(item) for item in first_plan.items]
    return MealPlanResponse(
        id=first_plan.id,
        week_start_date=first_plan.week_start_date,
        status=first_plan.status,
        items=items,
        created_at=first_plan.created_at,
        updated_at=first_plan.updated_at,
    )


@router.put("/plan/items/{item_id}", response_model=MealPlanItemResponse)
async def replace_plan_item(
    item_id: int,
    payload: MealPlanItemReplace,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    item = db.query(MealPlanItem).filter(MealPlanItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plan item not found")

    dish = db.query(Dish).filter(Dish.id == payload.dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    item.dish_id = dish.id
    item.is_manual = 1
    db.commit()
    db.refresh(item)
    await _broadcast_meal_plan_update(db)
    return _plan_item_to_response(item)


@router.delete("/plan/items/{item_id}")
async def remove_plan_item(
    item_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    item = db.query(MealPlanItem).filter(MealPlanItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plan item not found")
    db.delete(item)
    db.commit()
    await _broadcast_meal_plan_update(db)
    return {"status": "ok"}


@router.post("/plan/items", response_model=MealPlanItemResponse)
async def add_plan_item(
    payload: MealPlanItemAdd,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    week_start = _get_current_week_start()
    plan = db.query(MealPlan).filter(MealPlan.week_start_date == week_start).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No plan for current week")

    dish = db.query(Dish).filter(Dish.id == payload.dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    # Get max sort_order for this date+meal_type
    max_order = db.query(func.max(MealPlanItem.sort_order)).filter(
        and_(
            MealPlanItem.meal_plan_id == plan.id,
            MealPlanItem.date == payload.date,
            MealPlanItem.meal_type == payload.meal_type,
        )
    ).scalar() or -1

    item = MealPlanItem(
        meal_plan_id=plan.id,
        date=payload.date,
        meal_type=payload.meal_type,
        dish_id=dish.id,
        sort_order=max_order + 1,
        is_manual=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    await _broadcast_meal_plan_update(db)
    return _plan_item_to_response(item)


@router.post("/plan/confirm")
async def confirm_plan(
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    week_start = _get_current_week_start()
    plan = db.query(MealPlan).filter(MealPlan.week_start_date == week_start).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No plan for current week")
    plan.status = "confirmed"
    db.commit()
    await _broadcast_meal_plan_update(db)
    return {"status": "ok", "week_start_date": str(week_start)}


# ============================================================
# Meal History (Photo Recognition)
# ============================================================

@router.post("/history/recognize", response_model=PhotoRecognizeResponse)
async def recognize_photo(
    image: UploadFile = File(...),
    date_str: Optional[str] = Form(None, alias="date"),
    meal_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    # Save photo — convert non-JPG to JPG
    month_dir = datetime.now().strftime("%Y-%m")
    save_dir = os.path.join(settings.MEAL_PHOTO_DIR, month_dir)
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(save_dir, filename)

    content = await image.read()
    try:
        img = PILImage.open(io.BytesIO(content))
        # Fix EXIF orientation (common with Apple photos)
        img = PILImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img.save(file_path, "JPEG", quality=90)
        logger.info("Saved photo as JPEG (format=%s, exif-transposed): %s", img.format, file_path)
    except Exception as e:
        logger.warning("Pillow conversion failed, saving raw: %s", e)
        with open(file_path, "wb") as f:
            f.write(content)

    logger.info("Saved meal photo: %s (%d bytes)", file_path, os.path.getsize(file_path))

    # AI recognition
    dishes_raw = recognize_dishes(file_path)

    # Build message for empty results
    recognize_message = None
    if not dishes_raw:
        recognize_message = "AI 未能识别出菜品，请手动添加"
        logger.info("No dishes recognized from photo: %s", file_path)

    # Match with existing dishes
    recognized = []
    for d in dishes_raw:
        existing = db.query(Dish).filter(Dish.name == d["name"]).first()
        recognized.append(RecognizedDish(
            name=d["name"],
            matched=existing is not None,
            dish_id=existing.id if existing else None,
            category=d.get("category"),
        ))

    target_date = date.fromisoformat(date_str) if date_str else date.today()
    target_meal = meal_type or _infer_meal_type()

    # Relative path for storage
    rel_path = f"/data/meals/{month_dir}/{filename}"

    return PhotoRecognizeResponse(
        image_path=rel_path,
        recognized_dishes=recognized,
        date=target_date,
        meal_type=target_meal,
        recognize_message=recognize_message,
    )


@router.post("/history", response_model=MealLogResponse)
async def create_meal_log(
    payload: MealLogCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    logger.info("create_meal_log called: date=%s, meal_type=%s, dishes=%d, image=%s",
                payload.date, payload.meal_type, len(payload.dishes), payload.image_path)

    if not payload.dishes:
        raise HTTPException(status_code=400, detail="至少需要一道菜品")

    # Process dishes: create new ones if needed, track seen IDs to avoid duplicates
    dish_objects: Dict[int, Dish] = {}  # id -> Dish (dedup)
    new_dish_names: set = set()
    for d in payload.dishes:
        if d.dish_id:
            dish = db.query(Dish).filter(Dish.id == d.dish_id).first()
            if dish:
                if dish.id not in dish_objects:
                    dish_objects[dish.id] = dish
                continue
        # Create or find dish by name
        name = d.name.strip()
        if not name:
            continue
        # Check if we already processed this name in this request
        already_added = any(do.name == name for do in dish_objects.values())
        if already_added:
            continue
        dish = _get_or_create_dish(db, name, origin="photo")
        if dish.id and dish.id in dish_objects:
            continue  # same dish found by name as an earlier dish_id
        if dish.id:
            dish_objects[dish.id] = dish
        else:
            # Newly added, not yet flushed — use a temp key
            dish_objects[id(dish)] = dish
            new_dish_names.add(name)

    # Increment photo_count for all collected dishes
    for dish in dish_objects.values():
        dish.photo_count = (dish.photo_count or 0) + 1

    # Commit dishes first so new dishes get IDs
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to commit dishes: %s", e)
        raise HTTPException(status_code=500, detail="保存菜品时出错")

    for dish in dish_objects.values():
        db.refresh(dish)

    # Now build final_dishes with resolved IDs
    final_dishes = [{"dish_id": d.id, "name": d.name} for d in dish_objects.values()]
    logger.info("Resolved dishes: %s", final_dishes)

    log = MealLog(
        date=payload.date,
        meal_type=payload.meal_type,
        image_path=payload.image_path,
        dishes_json=json.dumps(final_dishes, ensure_ascii=False),
        confirmed=1,
        rated_by=payload.rated_by,
        rating=payload.rating,
        note=payload.note,
        liked_by=json.dumps(payload.liked_by or {}, ensure_ascii=False),
    )
    db.add(log)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to commit meal log: %s", e)
        raise HTTPException(status_code=500, detail="保存用餐记录时出错")
    db.refresh(log)

    # Update dish preferences for liked members (per-dish structure)
    liked_by_map: Dict[str, List[int]] = payload.liked_by or {}
    for d in final_dishes:
        dish_id = d.get("dish_id")
        dish_name = d.get("name", "")
        if not dish_id:
            continue
        member_ids = liked_by_map.get(dish_name, [])
        for member_id in member_ids:
            pref = db.query(DishPreference).filter(
                DishPreference.dish_id == dish_id,
                DishPreference.member_id == member_id,
            ).first()
            if pref:
                pref.like_count += 1
                pref.last_liked_at = beijing_now()
            else:
                pref = DishPreference(
                    dish_id=dish_id,
                    member_id=member_id,
                    like_count=1,
                    last_liked_at=beijing_now(),
                )
                db.add(pref)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("Failed to update dish preferences: %s", e)
        # Non-critical — meal log was already saved

    return MealLogResponse(
        id=log.id,
        date=log.date,
        meal_type=log.meal_type,
        image_path=log.image_path,
        dishes=[MealLogDishOutput(**d) for d in final_dishes],
        rating=log.rating,
        note=log.note,
        rated_by=log.rated_by,
        liked_by=_normalize_liked_by(log.liked_by),
        created_at=log.created_at,
    )


@router.get("/history", response_model=MealLogListResponse)
async def list_meal_logs(
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    query = db.query(MealLog)
    if start_date:
        query = query.filter(MealLog.date >= date.fromisoformat(start_date))
    if end_date:
        query = query.filter(MealLog.date <= date.fromisoformat(end_date))

    total = query.count()
    logs = query.order_by(MealLog.date.desc(), MealLog.created_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for log in logs:
        dishes = parse_json_field(log.dishes_json) or []
        items.append(MealLogResponse(
            id=log.id,
            date=log.date,
            meal_type=log.meal_type,
            image_path=log.image_path,
            dishes=[MealLogDishOutput(**d) for d in dishes if isinstance(d, dict)],
            rating=log.rating,
            note=log.note,
            rated_by=log.rated_by,
            liked_by=_normalize_liked_by(log.liked_by),
            created_at=log.created_at,
        ))

    return MealLogListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/history/stats", response_model=MealHistoryStatsResponse)
async def get_history_stats(
    days: int = 14,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    end = date.today()
    start = end - timedelta(days=days)

    logs = db.query(MealLog).filter(
        and_(MealLog.date >= start, MealLog.date <= end)
    ).order_by(MealLog.date).all()

    # Count dishes
    dish_counts: dict[str, dict] = {}
    total_meals = 0
    daily_map: dict[str, set] = {}

    for log in logs:
        day_key = log.date.isoformat()
        if day_key not in daily_map:
            daily_map[day_key] = set()
        total_meals += 1

        dishes = parse_json_field(log.dishes_json) or []
        for d in dishes:
            if not isinstance(d, dict) or "name" not in d:
                continue
            name = d["name"]
            daily_map[day_key].add(name)
            if name not in dish_counts:
                dish_counts[name] = {
                    "dish_id": d.get("dish_id"),
                    "name": name,
                    "count": 0,
                    "category": "",
                }
            dish_counts[name]["count"] += 1

    unique_dishes = len(dish_counts)
    total_dish_appearances = sum(v["count"] for v in dish_counts.values())
    repeat_rate = 1 - (unique_dishes / total_dish_appearances) if total_dish_appearances > 0 else 0.0

    # Top repeated (only dishes appearing > 1 time)
    top_repeated = sorted(
        [v for v in dish_counts.values() if v["count"] > 1],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    daily_counts = [
        {"date": k, "dish_count": len(v), "unique_count": len(v)}
        for k, v in sorted(daily_map.items())
    ]

    return MealHistoryStatsResponse(
        period={"start": start, "end": end},
        total_meals=total_meals,
        unique_dishes=unique_dishes,
        repeat_rate=round(repeat_rate, 2),
        top_repeated=top_repeated,
        daily_counts=daily_counts,
    )


# ============================================================
# Dish Preferences
# ============================================================

@router.get("/preferences", response_model=List[MemberPreferenceSummary])
async def get_dish_preferences(
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Get all members' liked dishes, aggregated from meal logs."""
    members = db.query(FamilyMember).all()
    result = []
    for member in members:
        prefs = db.query(DishPreference).filter(DishPreference.member_id == member.id) \
            .order_by(DishPreference.like_count.desc()).all()
        liked_dishes = []
        for p in prefs:
            dish = db.query(Dish).filter(Dish.id == p.dish_id).first()
            liked_dishes.append(DishPreferenceResponse(
                dish_id=p.dish_id,
                dish_name=dish.name if dish else "Unknown",
                member_id=member.id,
                member_name=member.name,
                like_count=p.like_count,
                last_liked_at=p.last_liked_at,
            ))
        result.append(MemberPreferenceSummary(
            member_id=member.id,
            member_name=member.name,
            liked_dishes=liked_dishes,
        ))
    return result


@router.get("/preferences/dish/{dish_id}", response_model=DishLikedByResponse)
async def get_dish_liked_by(
    dish_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Get which members like a specific dish."""
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    prefs = db.query(DishPreference).filter(DishPreference.dish_id == dish_id) \
        .order_by(DishPreference.like_count.desc()).all()
    liked_by = []
    for p in prefs:
        member = db.query(FamilyMember).filter(FamilyMember.id == p.member_id).first()
        liked_by.append({
            "member_id": p.member_id,
            "member_name": member.name if member else "Unknown",
            "like_count": p.like_count,
        })
    return DishLikedByResponse(
        dish_id=dish_id,
        dish_name=dish.name,
        liked_by=liked_by,
    )
