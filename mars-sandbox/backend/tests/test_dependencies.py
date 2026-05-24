"""Tests for FastAPI dependencies."""
import pytest
from unittest.mock import Mock
from fastapi import HTTPException, status
from app.dependencies import require_auth, current_user
from app.auth import create_session_token, COOKIE_NAME


class TestRequireAuth:
    """Test require_auth dependency."""

    @pytest.mark.asyncio
    async def test_require_auth_with_valid_cookie(self):
        """Should return user data when valid cookie is present."""
        mock_request = Mock()
        token = create_session_token("testuser")
        mock_request.cookies = {COOKIE_NAME: token}
        
        user = await require_auth(mock_request)
        
        assert user is not None
        assert user["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_require_auth_without_cookie(self):
        """Should raise 401 when no cookie is present."""
        mock_request = Mock()
        mock_request.cookies = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await require_auth(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Not authenticated"

    @pytest.mark.asyncio
    async def test_require_auth_with_invalid_cookie(self):
        """Should raise 401 when cookie contains invalid token."""
        mock_request = Mock()
        mock_request.cookies = {COOKIE_NAME: "invalid.token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await require_auth(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_require_auth_returns_correct_headers(self):
        """Should include WWW-Authenticate header in 401 response."""
        mock_request = Mock()
        mock_request.cookies = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await require_auth(mock_request)
        
        assert "WWW-Authenticate" in exc_info.value.headers
        assert exc_info.value.headers["WWW-Authenticate"] == "Cookie"


class TestCurrentUserAlias:
    """Test current_user alias."""

    def test_current_user_is_require_auth(self):
        """current_user should be an alias for require_auth."""
        assert current_user is require_auth
