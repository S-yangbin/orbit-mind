"""留言板命令组: board list/add/update/delete/pin"""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .context import get_client

app = typer.Typer(help="家庭留言板管理")
console = Console()


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command("list")
def board_list(
    json_out: bool = typer.Option(True, "--json/--no-json", help="JSON 输出"),
):
    """获取所有留言（置顶优先，按时间倒序）"""
    data = get_client().board_list()
    if json_out:
        _out(data)
    else:
        t = Table(title="留言板")
        t.add_column("ID", justify="right")
        t.add_column("内容")
        t.add_column("作者")
        t.add_column("颜色")
        t.add_column("置顶", justify="center")
        t.add_column("过期时间")
        t.add_column("创建时间")
        for msg in data.get("items", []):
            pin = "[green]✓[/green]" if msg.get("pinned") else ""
            t.add_row(
                str(msg.get("id")),
                msg.get("content", "")[:50],
                msg.get("author", ""),
                msg.get("color", ""),
                pin,
                str(msg.get("expires_at", "")),
                str(msg.get("created_at", ""))[:19],
            )
        console.print(t)


@app.command("add")
def board_add(
    content: str = typer.Argument(..., help="留言内容"),
    author: str = typer.Option("", "--author", "-a", help="作者"),
    color: str = typer.Option("yellow", "--color", "-c", help="颜色: yellow/red/blue/green/pink"),
    expires_at: Optional[str] = typer.Option(None, "--expires", "-e", help="过期日期 YYYY-MM-DD"),
):
    """创建新留言"""
    data = get_client().board_create(content=content, author=author, color=color, expires_at=expires_at)
    _out(data)


@app.command("update")
def board_update(
    message_id: int = typer.Argument(..., help="留言 ID"),
    content: Optional[str] = typer.Option(None, "--content", help="新内容"),
    author: Optional[str] = typer.Option(None, "--author", help="新作者"),
    color: Optional[str] = typer.Option(None, "--color", help="新颜色"),
    expires_at: Optional[str] = typer.Option(None, "--expires", help="新过期日期"),
):
    """更新留言"""
    data = get_client().board_update(message_id, content=content, author=author, color=color, expires_at=expires_at)
    _out(data)


@app.command("delete")
def board_delete(
    message_id: int = typer.Argument(..., help="留言 ID"),
):
    """删除留言"""
    _out(get_client().board_delete(message_id))


@app.command("pin")
def board_pin(
    message_id: int = typer.Argument(..., help="留言 ID"),
):
    """切换留言置顶状态"""
    _out(get_client().board_toggle_pin(message_id))
