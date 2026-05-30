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
    liked_dishes: Optional[List[Dict[str, Any]]] = None  # dynamically accumulated
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    allergies: Optional[List[str]] = None


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
    liked_by: Optional[List[int]] = None  # list of member_ids who liked


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
    liked_by: Optional[List[int]] = None
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
