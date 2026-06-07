"""Dashboard management routes — wallpaper refresh etc."""
from fastapi import APIRouter, Depends

from ..dependencies import require_auth_or_api_key
from ..ws.dashboard import refresh_wallpaper_and_broadcast

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.post("/refresh-wallpaper")
async def refresh_wallpaper(_user=Depends(require_auth_or_api_key)):
    """清除壁纸缓存并获取新壁纸，通过 WebSocket 推送到所有已连接的 Dashboard。

    认证方式：Cookie Session 或 X-API-Key header。
    """
    new_bg = await refresh_wallpaper_and_broadcast()
    if new_bg:
        return {"ok": True, "background_image": new_bg}
    return {"ok": False, "detail": "获取壁纸失败，已保留原有壁纸"}
