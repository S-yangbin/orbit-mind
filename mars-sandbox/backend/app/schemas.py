"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List
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
