"""SQLAlchemy ORM models."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, BigInteger, DateTime,
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
