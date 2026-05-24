"""Authentication: cookie-based session using itsdangerous."""
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, Response, HTTPException, status
from .config import settings

_serializer = URLSafeTimedSerializer(
    secret_key=settings.SECRET_KEY,
    salt="mars-sandbox-auth",
)

COOKIE_NAME = "mars_session"
MAX_AGE = 7 * 24 * 3600  # 7 days


def create_session_token(username: str) -> str:
    """Create a signed session token."""
    return _serializer.dumps({"username": username})


def verify_session_token(token: str) -> dict:
    """Verify and return session data."""
    try:
        return _serializer.loads(token, max_age=MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def set_auth_cookie(response: Response, username: str):
    """Set authentication cookie on response."""
    token = create_session_token(username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response):
    """Clear authentication cookie."""
    response.delete_cookie(key=COOKIE_NAME, path="/")


def get_current_user(request: Request) -> dict:
    """Get current authenticated user from cookie."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return verify_session_token(token)
