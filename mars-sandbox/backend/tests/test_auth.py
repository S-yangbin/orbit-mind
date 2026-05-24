"""Tests for authentication module."""
import pytest
from unittest.mock import Mock
from app.auth import (
    create_session_token,
    verify_session_token,
    set_auth_cookie,
    clear_auth_cookie,
    get_current_user,
    COOKIE_NAME,
    MAX_AGE,
)


class TestCreateSessionToken:
    """Test create_session_token function."""

    def test_create_token_returns_string(self):
        """Token should be a non-empty string."""
        token = create_session_token("testuser")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_contains_username(self):
        """Token should be verifiable and contain the username."""
        token = create_session_token("testuser")
        data = verify_session_token(token)
        assert data is not None
        assert data["username"] == "testuser"

    def test_create_token_different_users(self):
        """Different usernames should produce different tokens."""
        token1 = create_session_token("user1")
        token2 = create_session_token("user2")
        assert token1 != token2


class TestVerifySessionToken:
    """Test verify_session_token function."""

    def test_verify_valid_token(self):
        """Valid token should return session data."""
        token = create_session_token("testuser")
        data = verify_session_token(token)
        assert data is not None
        assert data["username"] == "testuser"

    def test_verify_invalid_token(self):
        """Invalid token should return None."""
        invalid_token = "invalid.token.here"
        data = verify_session_token(invalid_token)
        assert data is None

    def test_verify_empty_token(self):
        """Empty token should return None."""
        data = verify_session_token("")
        assert data is None

    def test_verify_tampered_token(self):
        """Tampered token should return None."""
        token = create_session_token("testuser")
        tampered = token + "tampered"
        data = verify_session_token(tampered)
        assert data is None


class TestSetAuthCookie:
    """Test set_auth_cookie function."""

    def test_set_cookie_calls_response(self):
        """Should call response.set_cookie with correct parameters."""
        mock_response = Mock()
        set_auth_cookie(mock_response, "testuser")
        
        mock_response.set_cookie.assert_called_once()
        call_kwargs = mock_response.set_cookie.call_args[1]
        
        assert call_kwargs["key"] == COOKIE_NAME
        assert call_kwargs["max_age"] == MAX_AGE
        assert call_kwargs["httponly"] is True
        assert call_kwargs["samesite"] == "lax"
        assert call_kwargs["path"] == "/"
        # Token should be a valid session token
        token_data = verify_session_token(call_kwargs["value"])
        assert token_data["username"] == "testuser"


class TestClearAuthCookie:
    """Test clear_auth_cookie function."""

    def test_clear_cookie_calls_response(self):
        """Should call response.delete_cookie with correct parameters."""
        mock_response = Mock()
        clear_auth_cookie(mock_response)
        
        mock_response.delete_cookie.assert_called_once_with(
            key=COOKIE_NAME,
            path="/",
        )


class TestGetCurrentUser:
    """Test get_current_user function."""

    def test_get_user_with_valid_cookie(self):
        """Should return user data when valid cookie is present."""
        mock_request = Mock()
        token = create_session_token("testuser")
        mock_request.cookies = {COOKIE_NAME: token}
        
        user = get_current_user(mock_request)
        
        assert user is not None
        assert user["username"] == "testuser"

    def test_get_user_without_cookie(self):
        """Should return None when no cookie is present."""
        mock_request = Mock()
        mock_request.cookies = {}
        
        user = get_current_user(mock_request)
        
        assert user is None

    def test_get_user_with_invalid_cookie(self):
        """Should return None when cookie contains invalid token."""
        mock_request = Mock()
        mock_request.cookies = {COOKIE_NAME: "invalid.token"}
        
        user = get_current_user(mock_request)
        
        assert user is None
