"""Authentication routes: login, logout, status."""
from fastapi import APIRouter, Response, Depends
from ..schemas import LoginRequest, LoginResponse, UserStatus
from ..config import settings
from ..auth import set_auth_cookie, clear_auth_cookie, get_current_user
from ..dependencies import current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response):
    if body.username == settings.AUTH_USERNAME and body.password == settings.AUTH_PASSWORD:
        set_auth_cookie(response, body.username)
        return LoginResponse(success=True, message="Login successful")
    return LoginResponse(success=False, message="Invalid credentials")


@router.post("/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"success": True, "message": "Logged out"}


@router.get("/me", response_model=UserStatus)
def me(user=Depends(current_user)):
    return UserStatus(authenticated=True)
