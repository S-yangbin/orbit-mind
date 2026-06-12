"""Dashboard management routes — wallpaper refresh etc."""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..dependencies import require_auth_or_api_key
from ..ws.dashboard import (
    refresh_wallpaper_and_broadcast,
    generate_ai_wallpaper_and_broadcast,
    list_wallpapers,
    set_wallpaper_and_broadcast,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class GenerateWallpaperRequest(BaseModel):
    prompt: Optional[str] = None


class SetWallpaperRequest(BaseModel):
    filename: str


@router.post("/refresh-wallpaper")
async def refresh_wallpaper(_user=Depends(require_auth_or_api_key)):
    """清除壁纸缓存并获取新壁纸，通过 WebSocket 推送到所有已连接的 Dashboard。

    认证方式：Cookie Session 或 X-API-Key header。
    """
    new_bg = await refresh_wallpaper_and_broadcast()
    if new_bg:
        return {"ok": True, "background_image": new_bg}
    return {"ok": False, "detail": "获取壁纸失败，已保留原有壁纸"}


@router.post("/generate-wallpaper")
async def generate_wallpaper(
    body: GenerateWallpaperRequest = GenerateWallpaperRequest(),
    _user=Depends(require_auth_or_api_key),
):
    """AI 生成壁纸并通过 WebSocket 推送到所有已连接的 Dashboard。

    可传入 prompt 自定义生成内容，不传则根据当前季节自动选择主题。
    生成耗时较长（约 30-90 秒），请耐心等待。

    认证方式：Cookie Session 或 X-API-Key header。
    """
    new_bg = await generate_ai_wallpaper_and_broadcast(body.prompt)
    if new_bg:
        return {"ok": True, "background_image": new_bg}
    return {"ok": False, "detail": "AI 壁纸生成失败，请稍后重试"}


@router.get("/wallpapers")
async def get_wallpapers(_user=Depends(require_auth_or_api_key)):
    """列出所有已生成的 AI 壁纸文件。"""
    return {"wallpapers": list_wallpapers()}


@router.post("/set-wallpaper")
async def set_wallpaper(
    body: SetWallpaperRequest,
    _user=Depends(require_auth_or_api_key),
):
    """设置指定壁纸并推送到所有已连接的 Dashboard。

    传入壁纸文件名（通过 GET /wallpapers 获取文件列表）。

    认证方式：Cookie Session 或 X-API-Key header。
    """
    new_bg = await set_wallpaper_and_broadcast(body.filename)
    if new_bg:
        return {"ok": True, "background_image": new_bg}
    return {"ok": False, "detail": f"壁纸文件不存在: {body.filename}"}
