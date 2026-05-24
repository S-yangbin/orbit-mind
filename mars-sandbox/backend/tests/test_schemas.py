"""Tests for Pydantic schemas."""
import pytest
from datetime import datetime
from app.schemas import (
    TagBase,
    TagCreate,
    TagUpdate,
    PageBase,
    PageCreate,
    PageUpdate,
    PageInDB,
    LoginRequest,
    LoginResponse,
    UserStatus,
    ScanStatus,
    ScanResult,
    NodeHeartbeatRequest,
    NodeResponse,
    NodeListResponse,
)


class TestTagSchemas:
    """Test tag-related schemas."""

    def test_tag_base(self):
        """TagBase should accept id and name."""
        tag = TagBase(id=1, name="test")
        assert tag.id == 1
        assert tag.name == "test"

    def test_tag_create(self):
        """TagCreate should accept name."""
        tag = TagCreate(name="new-tag")
        assert tag.name == "new-tag"

    def test_tag_update(self):
        """TagUpdate should accept name."""
        tag = TagUpdate(name="updated-tag")
        assert tag.name == "updated-tag"


class TestPageSchemas:
    """Test page-related schemas."""

    def test_page_base(self):
        """PageBase should accept required fields with defaults."""
        page = PageBase(slug="test-slug", title="Test Page")
        assert page.slug == "test-slug"
        assert page.title == "Test Page"
        assert page.description is None
        assert page.thumbnail is None
        assert page.entry_file == "index.html"

    def test_page_base_with_optional_fields(self):
        """PageBase should accept optional fields."""
        page = PageBase(
            slug="test-slug",
            title="Test Page",
            description="A test page",
            thumbnail="/thumbs/test.png",
            entry_file="main.html",
        )
        assert page.description == "A test page"
        assert page.thumbnail == "/thumbs/test.png"
        assert page.entry_file == "main.html"

    def test_page_create(self):
        """PageCreate should inherit from PageBase."""
        page = PageCreate(slug="new-page", title="New Page")
        assert page.slug == "new-page"
        assert page.title == "New Page"

    def test_page_update(self):
        """PageUpdate should accept optional fields."""
        update = PageUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.description is None
        assert update.tags is None

    def test_page_update_with_tags(self):
        """PageUpdate should accept tags list."""
        update = PageUpdate(tags=["tag1", "tag2"])
        assert update.tags == ["tag1", "tag2"]

    def test_page_in_db(self):
        """PageInDB should accept all fields."""
        now = datetime.utcnow()
        page = PageInDB(
            id=1,
            slug="test-slug",
            title="Test Page",
            created_at=now,
            updated_at=now,
            synced_at=now,
        )
        assert page.id == 1
        assert page.slug == "test-slug"
        assert page.is_customized == 0
        assert page.tags == []

    def test_page_in_db_display_title_priority(self):
        """display_title should follow priority: custom > scanned > title > slug."""
        now = datetime.utcnow()
        
        # Custom title takes priority
        page1 = PageInDB(
            id=1, slug="slug", title="Title",
            custom_title="Custom", scanned_title="Scanned",
            created_at=now, updated_at=now, synced_at=now,
        )
        assert page1.display_title == "Custom"
        
        # Scanned title if no custom
        page2 = PageInDB(
            id=2, slug="slug", title="Title",
            scanned_title="Scanned",
            created_at=now, updated_at=now, synced_at=now,
        )
        assert page2.display_title == "Scanned"
        
        # Title if no custom or scanned
        page3 = PageInDB(
            id=3, slug="slug", title="Title",
            created_at=now, updated_at=now, synced_at=now,
        )
        assert page3.display_title == "Title"
        
        # Slug as fallback (title is required in schema)
        page4 = PageInDB(
            id=4, slug="slug", title="slug",
            created_at=now, updated_at=now, synced_at=now,
        )
        assert page4.display_title == "slug"

    def test_page_in_db_display_description_priority(self):
        """display_description should follow priority: custom > scanned > description."""
        now = datetime.utcnow()
        
        # Custom description takes priority
        page1 = PageInDB(
            id=1, slug="slug", title="Title",
            custom_description="Custom", scanned_description="Scanned",
            description="Original",
            created_at=now, updated_at=now, synced_at=now,
        )
        assert page1.display_description == "Custom"
        
        # Scanned description if no custom
        page2 = PageInDB(
            id=2, slug="slug", title="Title",
            scanned_description="Scanned", description="Original",
            created_at=now, updated_at=now, synced_at=now,
        )
        assert page2.display_description == "Scanned"
        
        # Original description if no custom or scanned
        page3 = PageInDB(
            id=3, slug="slug", title="Title",
            description="Original",
            created_at=now, updated_at=now, synced_at=now,
        )
        assert page3.display_description == "Original"
        
        # Empty string as fallback
        page4 = PageInDB(
            id=4, slug="slug", title="Title",
            created_at=now, updated_at=now, synced_at=now,
        )
        assert page4.display_description == ""


class TestAuthSchemas:
    """Test authentication schemas."""

    def test_login_request(self):
        """LoginRequest should accept username and password."""
        req = LoginRequest(username="admin", password="secret")
        assert req.username == "admin"
        assert req.password == "secret"

    def test_login_response(self):
        """LoginResponse should accept success and message."""
        resp = LoginResponse(success=True, message="Login successful")
        assert resp.success is True
        assert resp.message == "Login successful"

    def test_user_status(self):
        """UserStatus should accept authenticated flag."""
        status = UserStatus(authenticated=True)
        assert status.authenticated is True


class TestScanSchemas:
    """Test scan-related schemas."""

    def test_scan_status_not_running(self):
        """ScanStatus should accept is_running flag."""
        status = ScanStatus(is_running=False)
        assert status.is_running is False
        assert status.last_scan_at is None
        assert status.last_result is None

    def test_scan_status_with_data(self):
        """ScanStatus should accept optional fields."""
        now = datetime.utcnow()
        status = ScanStatus(
            is_running=True,
            last_scan_at=now,
            last_result="Scan complete",
        )
        assert status.is_running is True
        assert status.last_scan_at == now
        assert status.last_result == "Scan complete"

    def test_scan_result(self):
        """ScanResult should accept task_id and message."""
        result = ScanResult(task_id="task-123", message="Scan started")
        assert result.task_id == "task-123"
        assert result.message == "Scan started"


class TestNodeSchemas:
    """Test node-related schemas."""

    def test_node_heartbeat_request_defaults(self):
        """NodeHeartbeatRequest should have sensible defaults."""
        req = NodeHeartbeatRequest(node_id="node-1")
        assert req.node_id == "node-1"
        assert req.hostname == ""
        assert req.ip == ""
        assert req.platform == ""
        assert req.version == "1.0.0"
        assert req.uptime_seconds == 0

    def test_node_heartbeat_request_full(self):
        """NodeHeartbeatRequest should accept all fields."""
        req = NodeHeartbeatRequest(
            node_id="node-1",
            hostname="my-host",
            ip="192.168.1.100",
            platform="linux",
            version="2.0.0",
            uptime_seconds=3600,
        )
        assert req.hostname == "my-host"
        assert req.ip == "192.168.1.100"
        assert req.version == "2.0.0"

    def test_node_response(self):
        """NodeResponse should accept all fields."""
        now = datetime.utcnow()
        node = NodeResponse(
            node_id="node-1",
            hostname="my-host",
            ip="192.168.1.100",
            platform="linux",
            version="1.0.0",
            status="online",
            last_heartbeat_at=now,
            uptime_seconds=3600,
            uptime="1h 0m",
        )
        assert node.node_id == "node-1"
        assert node.status == "online"
        assert node.uptime == "1h 0m"

    def test_node_list_response(self):
        """NodeListResponse should accept total counts and nodes list."""
        now = datetime.utcnow()
        node = NodeResponse(
            node_id="node-1",
            hostname="host-1",
            ip="192.168.1.1",
            platform="linux",
            version="1.0.0",
            status="online",
            uptime_seconds=3600,
        )
        response = NodeListResponse(
            total=1,
            online=1,
            offline=0,
            nodes=[node],
        )
        assert response.total == 1
        assert response.online == 1
        assert response.offline == 0
        assert len(response.nodes) == 1
        assert response.nodes[0].node_id == "node-1"
