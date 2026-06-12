"""Dashboard 命令组: 壁纸管理操作"""

import json
from typing import Optional

import typer

from .context import get_client

app = typer.Typer(help="家庭看板管理（壁纸刷新等）")


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command("refresh-wallpaper")
def refresh_wallpaper():
    """刷新 Dashboard 壁纸并推送到所有已连接的看板。

    清除壁纸缓存，从 Bing + Pexels 壁纸池中随机选取一张新壁纸，
    通过 WebSocket 实时推送到所有已连接的 Dashboard 前端页面。
    """
    result = get_client().refresh_wallpaper()
    _out(result)
    if result.get("ok"):
        typer.echo("\n壁纸已刷新，已推送到所有已连接的 Dashboard。", err=True)
    else:
        detail = result.get("detail", "未知错误")
        typer.echo(f"\n壁纸刷新失败: {detail}", err=True)
        raise typer.Exit(code=1)


@app.command("generate-wallpaper")
def generate_wallpaper(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="自定义生成提示词，不传则根据季节自动选择主题"),
):
    """AI 生成壁纸并推送到所有已连接的看板。

    使用大模型生成高清风景壁纸，并实时推送到所有已连接的 Dashboard 前端页面。
    生成耗时较长（约 30-90 秒），请耐心等待。
    """
    typer.echo("AI 壁纸生成中，请耐心等待...", err=True)
    result = get_client().generate_wallpaper(prompt=prompt)
    _out(result)
    if result.get("ok"):
        typer.echo("\nAI 壁纸已生成并推送到所有已连接的 Dashboard。", err=True)
    else:
        detail = result.get("detail", "未知错误")
        typer.echo(f"\nAI 壁纸生成失败: {detail}", err=True)
        raise typer.Exit(code=1)


@app.command("list-wallpapers")
def list_wallpapers():
    """列出所有已生成的 AI 壁纸。"""
    result = get_client().list_wallpapers()
    _out(result)
    wallpapers = result.get("wallpapers", [])
    if wallpapers:
        typer.echo(f"\n共 {len(wallpapers)} 张壁纸，可用 set-wallpaper 命令设置。", err=True)
    else:
        typer.echo("\n暂无已生成的壁纸，可用 generate-wallpaper 生成。", err=True)


@app.command("set-wallpaper")
def set_wallpaper(
    filename: str = typer.Argument(..., help="壁纸文件名（通过 list-wallpapers 查看）"),
):
    """设置指定壁纸并推送到所有已连接的看板。

    通过 list-wallpapers 命令查看可用壁纸文件名，然后使用本命令设置。
    """
    result = get_client().set_wallpaper(filename)
    _out(result)
    if result.get("ok"):
        typer.echo(f"\n壁纸已设置为 {filename}，已推送到所有已连接的 Dashboard。", err=True)
    else:
        detail = result.get("detail", "未知错误")
        typer.echo(f"\n设置壁纸失败: {detail}", err=True)
        raise typer.Exit(code=1)
