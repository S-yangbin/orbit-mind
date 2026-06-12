"""Pydantic schemas for API request/response validation."""
from datetime import datetime, date
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


# --- Tags ---
class TagBase(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    name: str


class TagUpdate(BaseModel):
    name: str


# --- Pages ---
class PageBase(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    entry_file: str = "index.html"
    category: str = "work"


class PageCreate(PageBase):
    pass


class PageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class PageInDB(PageBase):
    id: int
    content_hash: Optional[str] = None
    is_customized: int = 0
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    synced_at: datetime
    scanned_title: Optional[str] = None
    scanned_description: Optional[str] = None
    category: str = "work"
    tags: List[TagBase] = []

    class Config:
        from_attributes = True

    @property
    def display_title(self) -> str:
        return self.custom_title or self.scanned_title or self.title or self.slug

    @property
    def display_description(self) -> str:
        return self.custom_description or self.scanned_description or self.description or ""


# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str


class UserStatus(BaseModel):
    authenticated: bool


# --- Scan ---
class ScanStatus(BaseModel):
    is_running: bool
    last_scan_at: Optional[datetime] = None
    last_result: Optional[str] = None


class ScanResult(BaseModel):
    task_id: str
    message: str


# --- Nodes ---
class NodeHeartbeatRequest(BaseModel):
    node_id: str
    hostname: str = ""
    ip: str = ""
    platform: str = ""
    version: str = "1.0.0"
    uptime_seconds: int = 0


class NodeResponse(BaseModel):
    node_id: str
    hostname: str
    ip: str
    platform: str
    version: str
    status: str
    last_heartbeat_at: Optional[datetime] = None
    uptime_seconds: int
    uptime: str = ""

    class Config:
        from_attributes = True


class NodeListResponse(BaseModel):
    total: int
    online: int
    offline: int
    nodes: List[NodeResponse]


# --- Videos ---
class VideoUploadResponse(BaseModel):
    id: int
    title: str
    filename: str
    file_size: int
    status: str
    message: str

    class Config:
        from_attributes = True


class SegmentNoteResponse(BaseModel):
    id: int
    segment_id: int
    content: str
    note_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SegmentProgressResponse(BaseModel):
    id: int
    segment_id: int
    mastered: int
    loop_count: int
    last_practiced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoSegmentResponse(BaseModel):
    id: int
    video_id: int
    title: str
    segment_type: str
    start_time: int
    end_time: int
    transcription: Optional[str] = None
    sort_order: int
    notes: List[SegmentNoteResponse] = []
    progress: Optional[SegmentProgressResponse] = None

    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    id: int
    title: str
    filename: str
    file_path: str
    file_size: int
    duration: Optional[int] = None
    status: str
    oss_url: Optional[str] = None
    transcription_json: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    segments: List[VideoSegmentResponse] = []

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[VideoResponse]


class SegmentCreate(BaseModel):
    title: str
    segment_type: str = "qa"
    start_time: int
    end_time: int
    transcription: Optional[str] = None
    sort_order: int = 0


class SegmentUpdate(BaseModel):
    title: Optional[str] = None
    segment_type: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    transcription: Optional[str] = None
    sort_order: Optional[int] = None


class SegmentNoteCreate(BaseModel):
    content: str


class SegmentProgressUpdate(BaseModel):
    mastered: Optional[int] = None
    loop_count: Optional[int] = None
    last_practiced_at: Optional[datetime] = None


# ============================================================
# Meal Planning Schemas
# ============================================================

# --- Family Members ---
class FamilyMemberResponse(BaseModel):
    id: int
    name: str
    role: str
    avatar: str
    preferences: Optional[Dict[str, Any]] = None
    allergies: Optional[List[str]] = None
    board_color: Optional[str] = None  # hex color for board messages
    liked_dishes: Optional[List[Dict[str, Any]]] = None  # dynamically accumulated
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FamilyMemberCreate(BaseModel):
    name: str
    avatar: str = "\U0001f9d1"
    board_color: Optional[str] = None


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    allergies: Optional[List[str]] = None
    board_color: Optional[str] = None


class FamilyMemberListResponse(BaseModel):
    members: List[FamilyMemberResponse]


# --- Dishes ---
class DishResponse(BaseModel):
    id: int
    name: str
    category: str
    ingredients: Optional[List[str]] = None
    recipe: Optional[str] = None
    tags: Optional[List[str]] = None
    origin: str
    photo_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DishCreate(BaseModel):
    name: str
    category: str = "\u8364\u83dc"
    ingredients: Optional[List[str]] = None
    recipe: Optional[str] = None
    tags: Optional[List[str]] = None


class DishListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[DishResponse]


# --- Meal Plan ---
class MealPlanItemDish(BaseModel):
    id: int
    name: str
    category: str
    ingredients: Optional[List[str]] = None
    recipe: Optional[str] = None

    class Config:
        from_attributes = True


class MealPlanItemResponse(BaseModel):
    id: int
    date: date
    meal_type: str
    dish: MealPlanItemDish
    sort_order: int
    is_manual: int
    source: Optional[str] = None  # 'log' if from meal_log, 'plan' if from confirmed plan, None if AI draft

    class Config:
        from_attributes = True


class MealPlanResponse(BaseModel):
    id: int
    week_start_date: date
    status: str
    items: List[MealPlanItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MealPlanCurrentResponse(BaseModel):
    plan: Optional[MealPlanResponse] = None


class MealPlanGenerateRequest(BaseModel):
    week_start_date: Optional[date] = None


class MealPlanItemAdd(BaseModel):
    date: date
    meal_type: str
    dish_id: int


class MealPlanItemReplace(BaseModel):
    dish_id: int


# --- Meal Log (Photo Recognition) ---
class RecognizedDish(BaseModel):
    name: str
    matched: bool = False
    dish_id: Optional[int] = None
    category: Optional[str] = None


class PhotoRecognizeResponse(BaseModel):
    image_path: str
    recognized_dishes: List[RecognizedDish]
    date: date
    meal_type: str


class MealLogDishInput(BaseModel):
    dish_id: Optional[int] = None
    name: str


class MealLogCreate(BaseModel):
    image_path: str
    date: date
    meal_type: str
    dishes: List[MealLogDishInput]
    rating: Optional[int] = None
    note: Optional[str] = None
    rated_by: Optional[str] = None
    liked_by: Optional[Dict[str, List[int]]] = None  # dish_name -> [member_ids]


class MealLogDishOutput(BaseModel):
    dish_id: Optional[int] = None
    name: str


class MealLogResponse(BaseModel):
    id: int
    date: date
    meal_type: str
    image_path: str
    dishes: List[MealLogDishOutput]
    rating: Optional[int] = None
    note: Optional[str] = None
    rated_by: Optional[str] = None
    liked_by: Optional[Dict[str, List[int]]] = None  # dish_name -> [member_ids]
    created_at: datetime

    class Config:
        from_attributes = True


class MealLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[MealLogResponse]


class MealHistoryStatsResponse(BaseModel):
    period: Dict[str, date]
    total_meals: int
    unique_dishes: int
    repeat_rate: float
    top_repeated: List[Dict[str, Any]]
    daily_counts: List[Dict[str, Any]]


# --- Dish Preferences ---
class DishPreferenceResponse(BaseModel):
    dish_id: int
    dish_name: str
    member_id: int
    member_name: str
    like_count: int
    last_liked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MemberPreferenceSummary(BaseModel):
    member_id: int
    member_name: str
    liked_dishes: List[DishPreferenceResponse]


class DishLikedByResponse(BaseModel):
    dish_id: int
    dish_name: str
    liked_by: List[Dict[str, Any]]  # [{"member_id": 1, "member_name": "...", "like_count": 3}]


# ============================================================
# Cloud Drive Schemas
# ============================================================

class DriveFileResponse(BaseModel):
    id: int
    filename: str
    oss_key: str
    file_size: int
    content_type: str
    uploaded_by: str
    is_dir: int
    parent_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DriveFileListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[DriveFileResponse]
    breadcrumbs: List[Dict[str, Any]] = []  # [{"id": 1, "filename": "folder"}]


class DriveFileCreate(BaseModel):
    """Request body after frontend uploads to OSS directly."""
    filename: str
    oss_key: str
    file_size: int
    content_type: str = ""
    parent_id: Optional[int] = None


class DriveFolderCreate(BaseModel):
    """Create a new folder."""
    filename: str
    parent_id: Optional[int] = None


class DriveFileMove(BaseModel):
    """Move a file or folder to a target directory."""
    target_parent_id: Optional[int] = None  # None = root


class DriveFileCopy(BaseModel):
    """Copy a file to a target directory."""
    target_parent_id: Optional[int] = None  # None = root


class STSTokenResponse(BaseModel):
    access_key_id: str
    access_key_secret: str
    security_token: str
    expiration: str
    region: str
    bucket: str
    prefix: str


# --- Board Messages ---
class BoardMessageCreate(BaseModel):
    content: str
    author: str = ""
    color: str = "yellow"
    expires_at: Optional[date] = None


class BoardMessageUpdate(BaseModel):
    content: Optional[str] = None
    author: Optional[str] = None
    color: Optional[str] = None
    expires_at: Optional[date] = None


class BoardMessageResponse(BaseModel):
    id: int
    content: str
    author: str
    color: str
    pinned: int
    expires_at: Optional[date] = None
    acknowledged_by: Optional[List[int]] = None  # 已确认的家庭成员 ID 列表
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BoardMessageListResponse(BaseModel):
    items: List[BoardMessageResponse]


# ============================================================
# Learning Plan (Children's Daily Schedule) Schemas
# ============================================================

# --- Activity Type ---
class ActivityTypeResponse(BaseModel):
    id: int
    name: str
    icon: str
    category: str
    color: str
    is_preset: int
    sort_order: int
    child_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityTypeCreate(BaseModel):
    name: str
    icon: str = "\U0001f4da"
    category: str = "custom"
    color: str = "#4A90D9"


class ActivityTypeUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None


# --- Weekly Template ---
class WeeklyTemplateDayItem(BaseModel):
    day_of_week: int  # 0=Monday ... 6=Sunday
    activity_type_id: int
    sort_order: int = 0


class WeeklyTemplateResponse(BaseModel):
    id: int
    name: str
    child_id: Optional[int] = None
    is_active: int
    days: List[WeeklyTemplateDayItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WeeklyTemplateCreate(BaseModel):
    name: str = "默认周计划"
    days: List[WeeklyTemplateDayItem] = []  # day_of_week + activity_type_id list


# --- Daily Schedule ---
class DailyScheduleActivityType(BaseModel):
    id: int
    name: str
    icon: str
    color: str

    class Config:
        from_attributes = True


class DailyScheduleResponse(BaseModel):
    id: int
    date: date
    activity_type_id: int
    activity_type: Optional[DailyScheduleActivityType] = None
    completed: int
    completed_at: Optional[datetime] = None
    completion_note: Optional[str] = None
    sort_order: int
    is_override: int
    created_at: datetime

    class Config:
        from_attributes = True


class DailyScheduleCreate(BaseModel):
    date: date
    activity_type_id: int
    sort_order: int = 0


class DailyScheduleUpdate(BaseModel):
    completed: Optional[int] = None
    completion_note: Optional[str] = None


# --- Star Reward ---
class StarRewardResponse(BaseModel):
    id: int
    child_id: Optional[int] = None
    stars: int
    reason: Optional[str] = None
    related_schedule_id: Optional[int] = None
    awarded_by: str
    redeemed: int
    redeemed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StarRewardCreate(BaseModel):
    stars: int
    awarded_by: str
    reason: Optional[str] = None
    related_schedule_id: Optional[int] = None


class StarSummary(BaseModel):
    total_stars: int
    total_value: int  # total value in yuan (stars * 3)
    unredeemed_stars: int
    unredeemed_value: int  # unredeemed value in yuan
    recent_stars: List[StarRewardResponse] = []
