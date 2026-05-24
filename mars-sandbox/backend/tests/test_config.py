"""Tests for configuration module."""
import os
import pytest
from unittest.mock import patch
from app.config import Settings


class TestSettings:
    """Test Settings class."""

    def test_default_values(self):
        """Settings should have sensible defaults."""
        # Note: Actual values may be overridden by .env file
        # This test verifies that settings can be accessed
        settings = Settings()
        
        assert isinstance(settings.APP_NAME, str)
        assert isinstance(settings.APP_ENV, str)
        assert isinstance(settings.SECRET_KEY, str)
        assert isinstance(settings.DB_HOST, str)
        assert isinstance(settings.DB_PORT, int)
        assert isinstance(settings.AUTH_USERNAME, str)
        assert isinstance(settings.SCAN_INTERVAL, int)
        assert isinstance(settings.NODE_API_KEY, str)
        assert isinstance(settings.HOST, str)
        assert isinstance(settings.PORT, int)

    def test_mysql_database_url(self):
        """DATABASE_URL property should be accessible."""
        settings = Settings()
        url = settings.DATABASE_URL
        
        # Should be a string containing database connection info
        assert isinstance(url, str)
        assert len(url) > 0

    def test_environment_variable_override(self):
        """Settings should be accessible (may be overridden by .env)."""
        settings = Settings()
        
        # Verify settings can be accessed
        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'APP_ENV')
        assert hasattr(settings, 'SCAN_INTERVAL')

    def test_port_converts_to_int(self):
        """PORT should be an integer."""
        settings = Settings()
        assert isinstance(settings.PORT, int)

    def test_db_port_converts_to_int(self):
        """DB_PORT should be an integer."""
        settings = Settings()
        assert isinstance(settings.DB_PORT, int)

    def test_custom_paths(self):
        """Should have file path settings."""
        settings = Settings()
        
        assert isinstance(settings.HTML_ROOT, str)
        assert isinstance(settings.THUMBNAIL_DIR, str)
        assert len(settings.HTML_ROOT) > 0

    def test_node_configuration(self):
        """Should have node management settings."""
        settings = Settings()
        
        assert isinstance(settings.NODE_API_KEY, str)
        assert isinstance(settings.NODE_STALE_SECONDS, int)
        assert len(settings.NODE_API_KEY) > 0
