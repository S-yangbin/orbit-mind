"""Dashboard 命令组: 壁纸管理、语音播报、页面切换"""

import json
from typing import Optional

import typer

from .context import get_client

app = typer.Typer(help="家庭看板管理（壁纸、播报、翻页）")


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


@app.command("broadcast")
def broadcast(
    source: str = typer.Option(
        "messages",
        "--source", "-s",
        help="播报数据源: messages(留言板) / schedule(学习计划) / meals(今日菜谱) / text(自由文本)",
    ),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="自由播报文本 (仅 source=text 时)"),
    page: Optional[int] = typer.Option(None, "--page", "-p", help="播报时自动切换到指定页面 (0=家庭看板, 1=学习计划)"),
):
    """语音播报看板内容到所有已连接的 Dashboard。

    支持播报留言板、学习计划、今日菜谱或自定义文本。

    示例:
      mars-cli dashboard broadcast                    # 播报留言板
      mars-cli dashboard broadcast --source meals     # 播报今日菜谱
      mars-cli dashboard broadcast --source schedule  # 播报学习计划
      mars-cli dashboard broadcast --source text --text '该睡觉啦'  # 播报自定义文本
    """
    result = get_client().broadcast(source=source, text=text, page=page)
    _out(result)
    if result.get("ok"):
        broadcast_text = result.get("text", "")
        typer.echo(f"\n播报成功: {broadcast_text[:100]}..." if len(broadcast_text) > 100 else f"\n播报成功: {broadcast_text}", err=True)
    else:
        detail = result.get("detail", "未知错误")
        typer.echo(f"\n播报失败: {detail}", err=True)
        raise typer.Exit(code=1)


@app.command("switch-page")
def switch_page(
    page: int = typer.Argument(..., help="目标页面: 0=家庭看板, 1=学习计划"),
    auto_rotate: bool = typer.Option(False, "--auto-rotate", "-r", help="启动自动轮播模式"),
    interval: int = typer.Option(30, "--interval", "-i", help="自动轮播间隔秒数"),
):
    """远程控制 Dashboard 切换页面。

    可切换到指定页面，或启动自动轮播模式在两个页面间循环切换。

    示例:
      mars-cli dashboard switch-page 0              # 切换到家庭看板
      mars-cli dashboard switch-page 1              # 切换到学习计划
      mars-cli dashboard switch-page 0 --auto-rotate --interval 60  # 启动轮播
    """
    result = get_client().switch_page(page=page, auto_rotate=auto_rotate, interval=interval)
    _out(result)
    if result.get("ok"):
        page_name = "家庭看板" if page == 0 else "学习计划"
        if auto_rotate:
            typer.echo(f"\n已启动自动轮播，每 {interval} 秒切换一次。", err=True)
        else:
            typer.echo(f"\n已切换到{page_name}。", err=True)
    else:
        detail = result.get("detail", "未知错误")
        typer.echo(f"\n切换失败: {detail}", err=True)
        raise typer.Exit(code=1)


@app.command("screensaver")
def screensaver(
    enabled: bool = typer.Argument(..., help="true=进入屏保，false=唤醒看板"),
):
    """主动控制 Dashboard 屏保模式。

    示例:
      mars-cli dashboard screensaver true     # 立即进入屏保
      mars-cli dashboard screensaver false    # 唤醒看板
    """
    result = get_client().screensaver(enabled=enabled)
    _out(result)
    if result.get("ok"):
        state = "屏保已开启" if enabled else "看板已唤醒"
        typer.echo(f"\n{state}。", err=True)
    else:
        detail = result.get("detail", "未知错误")
        typer.echo(f"\n操作失败: {detail}", err=True)
        raise typer.Exit(code=1)
