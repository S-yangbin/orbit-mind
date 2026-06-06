"""云盘管理命令组: drive list/folders/mkdir/rm/move/copy/url/preview"""

import json
from typing import Optional

import typer

from .context import get_client

app = typer.Typer(help="云盘文件与文件夹管理")


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command("list")
def drive_list(
    parent_id: Optional[int] = typer.Option(None, "--parent", "-p", help="父文件夹 ID（不填则列根目录）"),
    q: Optional[str] = typer.Option(None, "-q", "--query", help="搜索文件名"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(50, "--page-size", help="每页数量"),
):
    """列出云盘文件"""
    _out(get_client().drive_list(parent_id=parent_id, q=q, page=page, page_size=page_size))


@app.command("folders")
def drive_folders():
    """列出所有文件夹（平铺列表，用于选择目标文件夹）"""
    _out(get_client().drive_list_folders())


@app.command("mkdir")
def drive_mkdir(
    name: str = typer.Argument(..., help="文件夹名称"),
    parent_id: Optional[int] = typer.Option(None, "--parent", "-p", help="父文件夹 ID"),
):
    """创建文件夹"""
    _out(get_client().drive_create_folder(filename=name, parent_id=parent_id))


@app.command("rm")
def drive_rm(
    file_id: int = typer.Argument(..., help="文件 ID"),
):
    """删除文件"""
    _out(get_client().drive_delete_file(file_id))


@app.command("rmdir")
def drive_rmdir(
    folder_id: int = typer.Argument(..., help="文件夹 ID"),
):
    """删除文件夹及其所有内容"""
    _out(get_client().drive_delete_folder(folder_id))


@app.command("move")
def drive_move(
    file_id: int = typer.Argument(..., help="文件/文件夹 ID"),
    target_parent_id: Optional[int] = typer.Argument(None, help="目标文件夹 ID（None=根目录）"),
):
    """移动文件或文件夹"""
    _out(get_client().drive_move(file_id, target_parent_id=target_parent_id))


@app.command("copy")
def drive_copy(
    file_id: int = typer.Argument(..., help="文件 ID"),
    target_parent_id: Optional[int] = typer.Argument(None, help="目标文件夹 ID（None=根目录）"),
):
    """复制文件"""
    _out(get_client().drive_copy(file_id, target_parent_id=target_parent_id))


@app.command("url")
def drive_url(
    oss_key: str = typer.Argument(..., help="OSS 对象 key"),
    expires_in: int = typer.Option(3600, "--expires", help="有效期（秒）"),
):
    """生成文件签名下载 URL"""
    _out(get_client().drive_signed_url(oss_key, expires_in=expires_in))


@app.command("preview")
def drive_preview(
    oss_key: str = typer.Argument(..., help="OSS 对象 key"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(200, "--lines", help="每页行数"),
):
    """预览文本文件内容（分页）"""
    _out(get_client().drive_preview_text(oss_key, page=page, page_size=page_size))
