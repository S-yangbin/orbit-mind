"""Dashboard 命令组: 壁纸刷新等看板管理操作"""

import json

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
