"""SQLAlchemy ORM models."""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, BigInteger, DateTime, Date,
    ForeignKey, SmallInteger, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .database import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(128), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    thumbnail = Column(String(512), nullable=True)
    entry_file = Column(String(255), nullable=False, default="index.html")
    content_hash = Column(String(64), nullable=True)
    is_customized = Column(SmallInteger, nullable=False, default=0)
    custom_title = Column(String(255), nullable=True)
    custom_description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    category = Column(String(32), nullable=False, default="work", server_default="work", index=True)
    synced_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    scanned_title = Column(String(255), nullable=True)
    scanned_description = Column(Text, nullable=True)

    tags = relationship("PageTag", back_populates="page", cascade="all, delete-orphan")

    @property
    def display_title(self) -> str:
        """Return user-edited title if available, else scanned, else slug."""
        return self.custom_title or self.scanned_title or self.title or self.slug

    @property
    def display_description(self) -> str:
        """Return user-edited description if available, else scanned, else description."""
        return self.custom_description or self.scanned_description or self.description or ""


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

    pages = relationship("PageTag", back_populates="tag", cascade="all, delete-orphan")


class PageTag(Base):
    __tablename__ = "page_tags"
    __table_args__ = (
        UniqueConstraint("page_id", "tag_id", name="uq_page_tag"),
    )

    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    page = relationship("Page", back_populates="tags")
    tag = relationship("Tag", back_populates="pages")


class Node(Base):
    """Home-agent node registry for heartbeat-based node discovery."""
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(128), nullable=False, unique=True, index=True)
    hostname = Column(String(255), nullable=True)
    ip = Column(String(64), nullable=True)
    platform = Column(String(255), nullable=True)
    version = Column(String(32), nullable=True, default="1.0.0")
    status = Column(String(16), nullable=False, default="offline")  # online / offline
    last_heartbeat_at = Column(DateTime, nullable=True)
    uptime_seconds = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Video(Base):
    """Uploaded video file metadata."""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)  # OSS relative path
    file_size = Column(BigInteger, nullable=False, default=0)
    duration = Column(Integer, nullable=True)  # seconds
    status = Column(String(32), nullable=False, default="pending")  # pending / processing / ready / error
    transcription_json = Column(Text, nullable=True)  # full ASR result JSON
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    segments = relationship("VideoSegment", back_populates="video", cascade="all, delete-orphan",
                            order_by="VideoSegment.start_time")


class VideoSegment(Base):
    """A labeled time segment within a video."""
    __tablename__ = "video_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    segment_type = Column(String(32), nullable=False, default="qa")  # intro / qa / explanation / outro / other
    start_time = Column(Integer, nullable=False)  # seconds
    end_time = Column(Integer, nullable=False)  # seconds
    transcription = Column(Text, nullable=True)  # subtitle text for this segment
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    video = relationship("Video", back_populates="segments")
    notes = relationship("SegmentNote", back_populates="segment", cascade="all, delete-orphan",
                         order_by="SegmentNote.created_at")
    progress = relationship("SegmentProgress", back_populates="segment", uselist=False,
                            cascade="all, delete-orphan")


class SegmentNote(Base):
    """User notes for a video segment."""
    __tablename__ = "segment_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    segment_id = Column(Integer, ForeignKey("video_segments.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    note_path = Column(String(1024), nullable=True)  # OSS markdown file path
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    segment = relationship("VideoSegment", back_populates="notes")


class SegmentProgress(Base):
    """Learning progress for a video segment."""
    __tablename__ = "segment_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    segment_id = Column(Integer, ForeignKey("video_segments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    mastered = Column(SmallInteger, nullable=False, default=0)  # 0=not mastered, 1=mastered
    loop_count = Column(Integer, nullable=False, default=0)
    last_practiced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    segment = relationship("VideoSegment", back_populates="progress")


# ============================================================
# Meal Planning Models
# ============================================================

class FamilyMember(Base):
    """Family member with taste preferences."""
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False, unique=True)  # father/mother/child/grandma or custom
    avatar = Column(String(16), nullable=False, default="\U0001f468")
    preferences = Column(Text, nullable=True)  # JSON: {"likes": [...], "dislikes": [...], "note": "..."}
    allergies = Column(Text, nullable=True)  # JSON: ["peanut", ...]
    board_color = Column(String(16), nullable=True)  # hex color for board messages
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Dish(Base):
    """Dish in the recipe database, accumulated over time."""
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(20), nullable=False, default="\u8364\u83dc")  # \u8364\u83dc/\u7d20\u83dc/\u6c64/\u4e3b\u98df/\u51c9\u83dc/\u65e9\u70b9
    ingredients = Column(Text, nullable=True)  # JSON: ["pork", "soy sauce", ...]
    recipe = Column(Text, nullable=True)  # brief cooking instructions
    tags = Column(Text, nullable=True)  # JSON: ["mild", "kid-friendly", ...]
    origin = Column(String(20), nullable=False, default="ai")  # ai / photo / manual
    photo_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MealPlan(Base):
    """Weekly meal plan."""
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_start_date = Column(Date, nullable=False, unique=True, index=True)
    status = Column(String(16), nullable=False, default="draft")  # draft / confirmed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("MealPlanItem", back_populates="plan", cascade="all, delete-orphan",
                         order_by="MealPlanItem.date, MealPlanItem.meal_type, MealPlanItem.sort_order")


class MealPlanItem(Base):
    """A single dish in a meal plan for a specific date and meal type."""
    __tablename__ = "meal_plan_items"
    __table_args__ = (
        UniqueConstraint("meal_plan_id", "date", "meal_type", "dish_id", name="uq_plan_item"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    meal_type = Column(String(16), nullable=False)  # breakfast / lunch / dinner
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_manual = Column(SmallInteger, nullable=False, default=0)  # 0=AI, 1=manual
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    plan = relationship("MealPlan", back_populates="items")
    dish = relationship("Dish")


class MealLog(Base):
    """Actual meal history record with photo."""
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    meal_type = Column(String(16), nullable=False)  # breakfast / lunch / dinner
    image_path = Column(String(512), nullable=False)
    dishes_json = Column(Text, nullable=False)  # JSON: [{"dish_id": 1, "name": "..."}, ...]
    confirmed = Column(SmallInteger, nullable=False, default=1)
    rated_by = Column(String(20), nullable=True)
    rating = Column(SmallInteger, nullable=True)  # 1-5
    note = Column(Text, nullable=True)
    liked_by = Column(Text, nullable=True)  # JSON: [member_id, ...]
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DishPreference(Base):
    """Tracks which family members like which dishes, accumulated from meal logs."""
    __tablename__ = "dish_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False, index=True)
    like_count = Column(Integer, nullable=False, default=0)  # number of times liked
    last_liked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("dish_id", "member_id", name="uq_dish_member_preference"),
    )


# ============================================================
# Cloud Drive Models
# ============================================================

class DriveFile(Base):
    """Cloud drive file or folder metadata stored in DB."""
    __tablename__ = "drive_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(512), nullable=False)
    oss_key = Column(String(512), nullable=False, unique=True, index=True)
    file_size = Column(BigInteger, nullable=False, default=0)
    content_type = Column(String(256), nullable=False, default="")
    uploaded_by = Column(String(64), nullable=False, default="")
    is_dir = Column(SmallInteger, nullable=False, default=0, index=True)  # 0=file, 1=directory
    parent_id = Column(Integer, ForeignKey("drive_files.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================================
# Board Message Models
# ============================================================

class BoardMessage(Base):
    """Family board message (sticky note style)."""
    __tablename__ = "board_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    author = Column(String(50), nullable=False, default="")
    color = Column(String(16), nullable=False, default="yellow")  # yellow/pink/blue/green
    pinned = Column(SmallInteger, nullable=False, default=0)
    expires_at = Column(Date, nullable=True)  # 过期日期，NULL 表示永不过期
    acknowledged_by = Column(Text, nullable=True)  # JSON: [member_id, ...] 已确认的家庭成员
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# Learning Plan (Children's Daily Schedule) Models
# ============================================================

class ActivityType(Base):
    """Activity type for children's daily schedule."""
    __tablename__ = "activity_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(16), nullable=False, default="\U0001f4da")  # emoji icon
    category = Column(String(20), nullable=False, default="custom")  # homework/reading/sports/arts/freeplay/custom
    color = Column(String(16), nullable=False, default="#4A90D9")  # hex color
    is_preset = Column(SmallInteger, nullable=False, default=0)  # 1=preset, 0=custom
    sort_order = Column(Integer, nullable=False, default=0)
    child_id = Column(Integer, nullable=True)  # reserved for multi-child support
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class WeeklyTemplate(Base):
    """Weekly schedule template."""
    __tablename__ = "weekly_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, default="默认周计划")
    child_id = Column(Integer, nullable=True)  # reserved for multi-child support
    is_active = Column(SmallInteger, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    days = relationship("WeeklyTemplateDay", back_populates="template", cascade="all, delete-orphan",
                         order_by="WeeklyTemplateDay.day_of_week, WeeklyTemplateDay.sort_order")


class WeeklyTemplateDay(Base):
    """A single activity in a weekly template day."""
    __tablename__ = "weekly_template_days"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("weekly_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    activity_type_id = Column(Integer, ForeignKey("activity_types.id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    template = relationship("WeeklyTemplate", back_populates="days")
    activity_type = relationship("ActivityType")


class DailySchedule(Base):
    """Actual daily schedule for a specific date."""
    __tablename__ = "daily_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    child_id = Column(Integer, nullable=True)  # reserved for multi-child support
    activity_type_id = Column(Integer, ForeignKey("activity_types.id", ondelete="CASCADE"), nullable=False)
    completed = Column(SmallInteger, nullable=False, default=0)  # 0=pending, 1=completed
    completed_at = Column(DateTime, nullable=True)
    completion_note = Column(Text, nullable=True)  # note on completion
    sort_order = Column(Integer, nullable=False, default=0)
    is_override = Column(SmallInteger, nullable=False, default=0)  # 1=manually adjusted, 0=from template
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    activity_type = relationship("ActivityType")
