"""星星奖励管理命令组: stars summary/list/add/redeem/delete"""

import json
from typing import Optional

import typer

from .context import get_client

app = typer.Typer(help="星星奖励管理（查看、颁发、兑换、删除）")


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command("summary")
def summary():
    """查看星星汇总（总数、可兑换金额、近期记录）"""
    _out(get_client().star_summary())


@app.command("list")
def list_stars(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="日期 YYYY-MM-DD，默认显示全部"),
):
    """星星记录列表"""
    _out(get_client().star_list(date=date))


@app.command("add")
def add(
    stars: int = typer.Argument(..., help="奖励的星星数量（1-10）"),
    awarded_by: str = typer.Option(..., "--awarded-by", "-a", help="颁发者名字"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="奖励原因"),
    schedule_id: Optional[int] = typer.Option(None, "--schedule-id", "-s", help="关联的学习计划项 ID"),
):
    """颁发星星奖励"""
    _out(get_client().star_add(stars=stars, awarded_by=awarded_by, reason=reason, schedule_id=schedule_id))


@app.command("redeem")
def redeem(
    star_id: int = typer.Argument(..., help="星星记录 ID"),
):
    """兑换星星"""
    _out(get_client().star_redeem(star_id))


@app.command("delete")
def delete(
    star_id: int = typer.Argument(..., help="星星记录 ID"),
):
    """删除星星记录（撤回误操作）"""
    _out(get_client().star_delete(star_id))
