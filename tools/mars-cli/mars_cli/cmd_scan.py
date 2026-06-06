"""目录扫描命令组: scan trigger/status"""

import json

import typer

from .context import get_client

app = typer.Typer(help="页面目录扫描管理")


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command("trigger")
def scan_trigger():
    """手动触发目录扫描（后台执行）"""
    _out(get_client().scan_trigger())


@app.command("status")
def scan_status():
    """获取当前扫描状态"""
    _out(get_client().scan_status())
