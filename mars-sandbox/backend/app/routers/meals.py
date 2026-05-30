"""Meal planning and dish recognition router."""
import json
import logging
import os
import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import require_auth
from ..models import FamilyMember, Dish, MealPlan, MealPlanItem, MealLog, DishPreference
from ..schemas import (
    FamilyMemberResponse, FamilyMemberUpdate, FamilyMemberListResponse,
    DishResponse, DishCreate, DishListResponse,
    MealPlanResponse, MealPlanCurrentResponse, MealPlanGenerateRequest,
    MealPlanItemResponse, MealPlanItemAdd, MealPlanItemReplace, MealPlanItemDish,
    PhotoRecognizeResponse, RecognizedDish,
    MealLogCreate, MealLogResponse, MealLogListResponse, MealLogDishOutput,
    MealHistoryStatsResponse, DishPreferenceResponse, MemberPreferenceSummary, DishLikedByResponse,
)
from ..services.ai_service import recognize_dishes, generate_monthly_weekend_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meals", tags=["meals"])


# ============================================================
# Helpers
# ============================================================

def _parse_json_field(value) -> any:
    """Parse a JSON string field, return parsed object or None."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _dish_to_response(dish: Dish) -> DishResponse:
    return DishResponse(
        id=dish.id,
        name=dish.name,
        category=dish.category,
        ingredients=_parse_json_field(dish.ingredients) or [],
        recipe=dish.recipe,
        tags=_parse_json_field(dish.tags) or [],
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
        preferences=_parse_json_field(m.preferences),
        allergies=_parse_json_field(m.allergies),
        liked_dishes=liked_dishes if liked_dishes else None,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _plan_item_to_response(item: MealPlanItem) -> MealPlanItemResponse:
    dish = item.dish
    return MealPlanItemResponse(
        id=item.id,
        date=item.date,
        meal_type=item.meal_type,
        dish=MealPlanItemDish(
            id=dish.id,
            name=dish.name,
            category=dish.category,
            ingredients=_parse_json_field(dish.ingredients) or [],
            recipe=dish.recipe,
        ),
        sort_order=item.sort_order,
        is_manual=item.is_manual,
    )


def _get_or_create_dish(db: Session, name: str, category: str = "荤菜", origin: str = "ai", recipe: str = "") -> Dish:
    """Find dish by name or create it."""
    dish = db.query(Dish).filter(Dish.name == name).first()
    if dish:
        return dish
    dish = Dish(name=name, category=category, origin=origin, recipe=recipe or None)
    db.add(dish)
    db.flush()
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


# ============================================================
# Meal Plan
# ============================================================

@router.get("/plan/current")
async def get_current_plan(
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """Return all plans for the next 4 weeks that contain weekend items."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    end_monday = monday + timedelta(days=28)
    plans = (
        db.query(MealPlan)
        .filter(MealPlan.week_start_date >= monday, MealPlan.week_start_date < end_monday)
        .order_by(MealPlan.week_start_date)
        .all()
    )
    if not plans:
        return {"plans": []}

    result = []
    for plan in plans:
        weekend_items = [
            _plan_item_to_response(item)
            for item in plan.items
            if item.date.weekday() in (5, 6)  # Sat=5, Sun=6
        ]
        if weekend_items:
            result.append({
                "id": plan.id,
                "week_start_date": plan.week_start_date,
                "status": plan.status,
                "items": weekend_items,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
            })
    return {"plans": result}


@router.post("/plan/generate", response_model=MealPlanResponse)
async def generate_plan(
    payload: MealPlanGenerateRequest,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    # Start from today, generate 4 weeks of weekends
    today = date.today()
    start_date = payload.week_start_date or today

    # Delete existing draft plans for the next 4 weeks
    for week_offset in range(4):
        week_start = start_date + timedelta(days=week_offset * 7)
        monday = week_start - timedelta(days=week_start.weekday())
        existing = db.query(MealPlan).filter(MealPlan.week_start_date == monday).first()
        if existing and existing.status != "confirmed":
            db.delete(existing)
    db.flush()

    # Collect members
    _seed_default_members(db)
    members = db.query(FamilyMember).order_by(FamilyMember.id).all()
    member_data = []
    for m in members:
        preferences = _parse_json_field(m.preferences) or {}
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
            "allergies": _parse_json_field(m.allergies) or [],
        })

    # Collect recent dishes (last 4 weeks)
    four_weeks_ago = date.today() - timedelta(days=28)
    recent_logs = db.query(MealLog).filter(MealLog.date >= four_weeks_ago).all()
    recent_dish_names = set()
    for log in recent_logs:
        dishes = _parse_json_field(log.dishes_json) or []
        for d in dishes:
            if isinstance(d, dict) and "name" in d:
                recent_dish_names.add(d["name"])

    # Call AI for monthly weekend plan
    plan_data = generate_monthly_weekend_plan(member_data, list(recent_dish_names), start_date)
    if not plan_data:
        raise HTTPException(status_code=502, detail="AI failed to generate plan")

    # Create plans per week (group weekend days into their respective weeks)
    plans_by_week = {}  # week_start_date -> plan object
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
            if not plan_obj:
                plan_obj = MealPlan(week_start_date=monday, status="draft")
                db.add(plan_obj)
                db.flush()
            plans_by_week[monday] = plan_obj

        plan_obj = plans_by_week[monday]
        meals = day_entry.get("meals", {})
        for meal_type in ["lunch", "dinner"]:
            dish_list = meals.get(meal_type, [])
            for idx, dish_info in enumerate(dish_list):
                name = dish_info.get("name", "").strip()
                if not name:
                    continue
                category = dish_info.get("category", "荤菜")
                recipe = dish_info.get("recipe", "")
                dish = _get_or_create_dish(db, name, category, origin="ai", recipe=recipe)
                item = MealPlanItem(
                    meal_plan_id=plan_obj.id,
                    date=day_date,
                    meal_type=meal_type,
                    dish_id=dish.id,
                    sort_order=idx,
                    is_manual=0,
                )
                db.add(item)

    db.commit()

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
    # Save photo
    month_dir = datetime.now().strftime("%Y-%m")
    save_dir = os.path.join(settings.MEAL_PHOTO_DIR, month_dir)
    os.makedirs(save_dir, exist_ok=True)

    ext = os.path.splitext(image.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(save_dir, filename)

    content = await image.read()
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info("Saved meal photo: %s (%d bytes)", file_path, len(content))

    # AI recognition
    dishes_raw = recognize_dishes(file_path)

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
    )


@router.post("/history", response_model=MealLogResponse)
async def create_meal_log(
    payload: MealLogCreate,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    # Process dishes: create new ones if needed
    final_dishes = []
    for d in payload.dishes:
        if d.dish_id:
            dish = db.query(Dish).filter(Dish.id == d.dish_id).first()
            if dish:
                dish.photo_count += 1
                final_dishes.append({"dish_id": dish.id, "name": dish.name})
                continue
        # Create new dish
        dish = _get_or_create_dish(db, d.name, origin="photo")
        dish.photo_count += 1
        final_dishes.append({"dish_id": dish.id, "name": dish.name})

    log = MealLog(
        date=payload.date,
        meal_type=payload.meal_type,
        image_path=payload.image_path,
        dishes_json=json.dumps(final_dishes, ensure_ascii=False),
        confirmed=1,
        rated_by=payload.rated_by,
        rating=payload.rating,
        note=payload.note,
        liked_by=json.dumps(payload.liked_by or [], ensure_ascii=False),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Update dish preferences for liked members
    liked_member_ids = payload.liked_by or []
    for d in final_dishes:
        dish_id = d.get("dish_id")
        if not dish_id:
            continue
        for member_id in liked_member_ids:
            pref = db.query(DishPreference).filter(
                DishPreference.dish_id == dish_id,
                DishPreference.member_id == member_id,
            ).first()
            if pref:
                pref.like_count += 1
                pref.last_liked_at = datetime.utcnow()
            else:
                pref = DishPreference(
                    dish_id=dish_id,
                    member_id=member_id,
                    like_count=1,
                    last_liked_at=datetime.utcnow(),
                )
                db.add(pref)
    db.commit()

    return MealLogResponse(
        id=log.id,
        date=log.date,
        meal_type=log.meal_type,
        image_path=log.image_path,
        dishes=[MealLogDishOutput(**d) for d in final_dishes],
        rating=log.rating,
        note=log.note,
        rated_by=log.rated_by,
        liked_by=_parse_json_field(log.liked_by) or [],
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
        dishes = _parse_json_field(log.dishes_json) or []
        items.append(MealLogResponse(
            id=log.id,
            date=log.date,
            meal_type=log.meal_type,
            image_path=log.image_path,
            dishes=[MealLogDishOutput(**d) for d in dishes if isinstance(d, dict)],
            rating=log.rating,
            note=log.note,
            rated_by=log.rated_by,
            liked_by=_parse_json_field(log.liked_by) or [],
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

        dishes = _parse_json_field(log.dishes_json) or []
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
