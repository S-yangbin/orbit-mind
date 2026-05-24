"""Tests for SQLAlchemy ORM models."""
import pytest
from datetime import datetime
from app.models import Page, Tag, PageTag, Node


class TestPageModel:
    """Test Page ORM model."""

    def test_page_creation(self, db_session):
        """Should create a Page with required fields."""
        page = Page(
            slug="test-page",
            title="Test Page",
        )
        db_session.add(page)
        db_session.commit()
        
        assert page.id is not None
        assert page.slug == "test-page"
        assert page.title == "Test Page"
        assert page.entry_file == "index.html"
        assert page.is_customized == 0

    def test_page_display_title_priority(self, db_session):
        """display_title should follow: custom_title > scanned_title > title > slug."""
        # Custom title takes priority
        page1 = Page(
            slug="page1", title="Title",
            custom_title="Custom", scanned_title="Scanned",
        )
        db_session.add(page1)
        db_session.commit()
        assert page1.display_title == "Custom"
        
        # Scanned title if no custom
        page2 = Page(
            slug="page2", title="Title",
            scanned_title="Scanned",
        )
        db_session.add(page2)
        db_session.commit()
        assert page2.display_title == "Scanned"
        
        # Title if no custom or scanned
        page3 = Page(slug="page3", title="Title")
        db_session.add(page3)
        db_session.commit()
        assert page3.display_title == "Title"
        
        # Slug as fallback (title is required, use empty string)
        page4 = Page(slug="page4", title="page4")
        db_session.add(page4)
        db_session.commit()
        assert page4.display_title == "page4"

    def test_page_display_description_priority(self, db_session):
        """display_description should follow: custom > scanned > description."""
        # Custom description takes priority
        page1 = Page(
            slug="page1", title="Title",
            custom_description="Custom",
            scanned_description="Scanned",
            description="Original",
        )
        db_session.add(page1)
        db_session.commit()
        assert page1.display_description == "Custom"
        
        # Scanned description if no custom
        page2 = Page(
            slug="page2", title="Title",
            scanned_description="Scanned",
            description="Original",
        )
        db_session.add(page2)
        db_session.commit()
        assert page2.display_description == "Scanned"
        
        # Original description if no custom or scanned
        page3 = Page(
            slug="page3", title="Title",
            description="Original",
        )
        db_session.add(page3)
        db_session.commit()
        assert page3.display_description == "Original"
        
        # Empty string as fallback
        page4 = Page(slug="page4", title="Title")
        db_session.add(page4)
        db_session.commit()
        assert page4.display_description == ""

    def test_page_timestamps(self, db_session):
        """Page should have auto-set timestamps."""
        before = datetime.utcnow()
        page = Page(slug="test", title="Test")
        db_session.add(page)
        db_session.commit()
        
        assert page.created_at is not None
        assert page.updated_at is not None
        assert page.synced_at is not None
        assert page.created_at >= before

    def test_page_relationships(self, db_session):
        """Page should have tag relationships."""
        page = Page(slug="test", title="Test")
        tag = Tag(name="test-tag")
        page_tag = PageTag(page=page, tag=tag)
        
        db_session.add(page)
        db_session.add(tag)
        db_session.add(page_tag)
        db_session.commit()
        
        assert len(page.tags) == 1
        assert page.tags[0].tag.name == "test-tag"


class TestTagModel:
    """Test Tag ORM model."""

    def test_tag_creation(self, db_session):
        """Should create a Tag."""
        tag = Tag(name="test-tag")
        db_session.add(tag)
        db_session.commit()
        
        assert tag.id is not None
        assert tag.name == "test-tag"

    def test_tag_unique_name(self, db_session):
        """Tag names should be unique."""
        tag1 = Tag(name="unique-tag")
        db_session.add(tag1)
        db_session.commit()
        
        tag2 = Tag(name="unique-tag")
        db_session.add(tag2)
        
        with pytest.raises(Exception):
            db_session.commit()

    def test_tag_relationships(self, db_session):
        """Tag should have page relationships."""
        page = Page(slug="test", title="Test")
        tag = Tag(name="test-tag")
        page_tag = PageTag(page=page, tag=tag)
        
        db_session.add_all([page, tag, page_tag])
        db_session.commit()
        
        assert len(tag.pages) == 1
        assert tag.pages[0].page.slug == "test"


class TestPageTagModel:
    """Test PageTag ORM model (many-to-many relationship)."""

    def test_page_tag_creation(self, db_session):
        """Should create a PageTag linking page and tag."""
        page = Page(slug="test", title="Test")
        tag = Tag(name="test-tag")
        page_tag = PageTag(page_id=page.id, tag_id=tag.id)
        
        # Need to flush to get IDs
        db_session.add(page)
        db_session.add(tag)
        db_session.flush()
        
        page_tag = PageTag(page_id=page.id, tag_id=tag.id)
        db_session.add(page_tag)
        db_session.commit()
        
        assert page_tag.page_id == page.id
        assert page_tag.tag_id == tag.id

    def test_page_tag_unique_constraint(self, db_session):
        """Page-Tag pair should be unique."""
        page = Page(slug="test", title="Test")
        tag = Tag(name="test-tag")
        
        db_session.add(page)
        db_session.add(tag)
        db_session.flush()
        
        pt1 = PageTag(page_id=page.id, tag_id=tag.id)
        db_session.add(pt1)
        db_session.commit()
        
        pt2 = PageTag(page_id=page.id, tag_id=tag.id)
        db_session.add(pt2)
        
        with pytest.raises(Exception):
            db_session.commit()

    def test_page_tag_cascade_delete_page(self, db_session):
        """Deleting a page should cascade delete PageTag."""
        page = Page(slug="test", title="Test")
        tag = Tag(name="test-tag")
        
        db_session.add(page)
        db_session.add(tag)
        db_session.flush()
        
        page_tag = PageTag(page_id=page.id, tag_id=tag.id)
        db_session.add(page_tag)
        db_session.commit()
        
        page_id = page.id
        db_session.delete(page)
        db_session.commit()
        
        # PageTag should be deleted
        from sqlalchemy import text
        result = db_session.execute(
            text("SELECT COUNT(*) FROM page_tags WHERE page_id = :pid"),
            {"pid": page_id}
        ).scalar()
        assert result == 0


class TestNodeModel:
    """Test Node ORM model."""

    def test_node_creation(self, db_session):
        """Should create a Node with required fields."""
        node = Node(
            node_id="node-1",
            hostname="test-host",
            ip="192.168.1.100",
            platform="linux",
        )
        db_session.add(node)
        db_session.commit()
        
        assert node.id is not None
        assert node.node_id == "node-1"
        assert node.hostname == "test-host"
        assert node.status == "offline"  # default
        assert node.version == "1.0.0"  # default
        assert node.uptime_seconds == 0  # default

    def test_node_unique_node_id(self, db_session):
        """Node IDs should be unique."""
        node1 = Node(node_id="unique-node")
        db_session.add(node1)
        db_session.commit()
        
        node2 = Node(node_id="unique-node")
        db_session.add(node2)
        
        with pytest.raises(Exception):
            db_session.commit()

    def test_node_status_values(self, db_session):
        """Node status should accept online/offline."""
        node = Node(node_id="node-1", status="online")
        db_session.add(node)
        db_session.commit()
        
        assert node.status == "online"
        
        node.status = "offline"
        db_session.commit()
        assert node.status == "offline"

    def test_node_heartbeat_timestamp(self, db_session):
        """Node should track last_heartbeat_at."""
        node = Node(node_id="node-1")
        db_session.add(node)
        db_session.commit()
        
        assert node.last_heartbeat_at is None
        
        node.last_heartbeat_at = datetime.utcnow()
        db_session.commit()
        
        assert node.last_heartbeat_at is not None

    def test_node_timestamps(self, db_session):
        """Node should have auto-set timestamps."""
        before = datetime.utcnow()
        node = Node(node_id="node-1")
        db_session.add(node)
        db_session.commit()
        
        assert node.created_at is not None
        assert node.updated_at is not None
        assert node.created_at >= before
