"""标签管理命令组: tags list/create/update/delete"""

import json

import typer

from .context import get_client

app = typer.Typer(help="标签管理")


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command("list")
def tags_list():
    """列出所有标签及关联页面数量"""
    _out(get_client().list_tags())


@app.command("create")
def tags_create(
    name: str = typer.Argument(..., help="标签名称"),
):
    """创建新标签"""
    _out(get_client().create_tag(name))


@app.command("update")
def tags_update(
    tag_id: int = typer.Argument(..., help="标签 ID"),
    name: str = typer.Argument(..., help="新名称"),
):
    """重命名标签"""
    _out(get_client().update_tag(tag_id, name))


@app.command("delete")
def tags_delete(
    tag_id: int = typer.Argument(..., help="标签 ID"),
):
    """删除标签"""
    _out(get_client().delete_tag(tag_id))
