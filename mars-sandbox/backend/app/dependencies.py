"""FastAPI dependency injections."""
import hmac
from typing import Optional
from fastapi import Depends, HTTPException, Header, Request, status
from .auth import get_current_user
from .config import settings
from .database import get_db


async def require_auth(
    request: Request,
):
    """Dependency that requires authentication."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return user


# Alias for cleaner usage in routers
current_user = require_auth


def verify_node_api_key(x_api_key: str = Header(...)):
    """Verify X-API-Key header using timing-safe comparison.

    Used by node-facing endpoints (heartbeat, commands) to authenticate
    home-agent and CLI clients.
    """
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.NODE_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )


async def require_auth_or_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None),
):
    """支持双重认证：cookie session 或 X-API-Key header

    前端使用 cookie 认证，CLI/API 客户端使用 API Key 认证。
    任一方式通过即可访问。
    """
    # 方式1: cookie session 认证
    user = get_current_user(request)
    if user is not None:
        return user

    # 方式2: X-API-Key 认证 (timing-safe)
    if x_api_key and hmac.compare_digest(x_api_key, settings.NODE_API_KEY):
        return {"username": "api-client"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Cookie"},
    )
