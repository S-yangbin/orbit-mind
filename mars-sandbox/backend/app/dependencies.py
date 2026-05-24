"""FastAPI dependency injections."""
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

    # 方式2: X-API-Key 认证
    if x_api_key and x_api_key == settings.NODE_API_KEY:
        return {"username": "api-client"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Cookie"},
    )
