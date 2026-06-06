"""页面管理命令组: pages list/get/update/delete"""

import json
from typing import Optional, List

import typer

from .context import get_client

app = typer.Typer(help="托管页面管理")


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command("list")
def pages_list(
    q: Optional[str] = typer.Option(None, "-q", "--query", help="搜索关键词"),
    tag: Optional[str] = typer.Option(None, "--tag", help="按标签过滤"),
    category: Optional[str] = typer.Option(None, "--category", help="按分类过滤"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", help="每页数量"),
):
    """查询页面列表（支持搜索、标签、分类过滤）"""
    _out(get_client().list_pages(q=q, tag=tag, category=category, page=page, page_size=page_size))


@app.command("get")
def pages_get(
    page_id: int = typer.Argument(..., help="页面 ID"),
):
    """获取页面详情"""
    _out(get_client().get_page(page_id))


@app.command("update")
def pages_update(
    page_id: int = typer.Argument(..., help="页面 ID"),
    title: Optional[str] = typer.Option(None, "--title", help="新标题"),
    description: Optional[str] = typer.Option(None, "--description", help="新描述"),
    category: Optional[str] = typer.Option(None, "--category", help="新分类"),
    tags: Optional[str] = typer.Option(None, "--tags", help="标签列表，逗号分隔"),
):
    """更新页面元数据"""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    _out(get_client().update_page(page_id, title=title, description=description, tags=tag_list, category=category))


@app.command("delete")
def pages_delete(
    page_id: int = typer.Argument(..., help="页面 ID"),
):
    """删除页面记录（不删除文件）"""
    _out(get_client().delete_page(page_id))
