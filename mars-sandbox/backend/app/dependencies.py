"""FastAPI dependency injections."""
from fastapi import Depends, HTTPException, Request, status
from .auth import get_current_user
from .database import get_db


async def require_auth(
    request: Request,
):
    user = get_current_user(request)
    """Dependency that requires authentication."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return user


# Alias for cleaner usage in routers
current_user = require_auth
