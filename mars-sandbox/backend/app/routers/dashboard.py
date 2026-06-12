"""Dashboard management routes — wallpaper refresh etc."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..database import SessionLocal
from ..dependencies import require_auth_or_api_key
from ..ws.dashboard import (
    refresh_wallpaper_and_broadcast,
    generate_ai_wallpaper_and_broadcast,
    list_wallpapers,
    set_wallpaper_and_broadcast,
    broadcast_tts,
    broadcast_switch_page,
    broadcast_screensaver,
    format_board_messages,
    format_today_schedule,
    format_today_meals,
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


class BroadcastRequest(BaseModel):
    source: str = "messages"  # messages | schedule | meals | text
    text: Optional[str] = None  # 仅 source=text 时使用
    page: Optional[int] = None  # 播报时自动切换到指定页面


@router.post("/broadcast")
async def broadcast(
    body: BroadcastRequest,
    _user=Depends(require_auth_or_api_key),
):
    """语音播报接口：根据数据源自动查询并格式化为自然语言，通过 WS 广播到所有 Dashboard。

    数据源：
    - messages: 播报留言板内容（默认）
    - schedule: 播报今日学习计划
    - meals: 播报今日菜谱
    - text: 播报自由文本（需传 text 参数）

    认证方式：Cookie Session 或 X-API-Key header。
    """
    if body.source == "text":
        if not body.text:
            raise HTTPException(status_code=400, detail="source=text 时必须提供 text 参数")
        tts_text = body.text
    else:
        # 从数据库查询并格式化
        db = SessionLocal()
        try:
            if body.source == "messages":
                tts_text = format_board_messages(db)
            elif body.source == "schedule":
                tts_text = format_today_schedule(db)
            elif body.source == "meals":
                tts_text = format_today_meals(db)
            else:
                raise HTTPException(status_code=400, detail=f"未知的 source: {body.source}")
        finally:
            db.close()

    await broadcast_tts(tts_text, body.page)
    return {"ok": True, "text": tts_text}


class SwitchPageRequest(BaseModel):
    page: int  # 0=家庭看板, 1=学习计划
    auto_rotate: bool = False  # 是否自动轮播
    interval: int = 30  # 轮播间隔秒数


@router.post("/switch-page")
async def switch_page(
    body: SwitchPageRequest,
    _user=Depends(require_auth_or_api_key),
):
    """远程控制 Dashboard 切换页面。

    支持切换到指定页面或启动自动轮播模式。

    认证方式：Cookie Session 或 X-API-Key header。
    """
    if body.page not in (0, 1):
        raise HTTPException(status_code=400, detail="page 必须是 0 或 1")
    await broadcast_switch_page(body.page, body.auto_rotate, body.interval)
    return {"ok": True, "page": body.page, "auto_rotate": body.auto_rotate, "interval": body.interval}


class ScreensaverRequest(BaseModel):
    enabled: bool  # True=进入屏保，False=唤醒


@router.post("/screensaver")
async def screensaver(
    body: ScreensaverRequest,
    _user=Depends(require_auth_or_api_key),
):
    """主动控制 Dashboard 屏保模式。

    enabled=true 立即进入屏保，enabled=false 唤醒看板。

    认证方式：Cookie Session 或 X-API-Key header。
    """
    await broadcast_screensaver(body.enabled)
    return {"ok": True, "enabled": body.enabled}
