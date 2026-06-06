"""视频学习管理命令组: videos list/get/process + segments/notes/progress"""

import json
from typing import Optional

import typer

from .context import get_client

app = typer.Typer(help="视频学习管理（分段、笔记、进度）")


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command("list")
def videos_list(
    q: Optional[str] = typer.Option(None, "-q", "--query", help="搜索关键词"),
    status: Optional[str] = typer.Option(None, "--status", help="按状态过滤"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", help="每页数量"),
):
    """查询视频列表"""
    _out(get_client().videos_list(q=q, status=status, page=page, page_size=page_size))


@app.command("get")
def videos_get(
    video_id: int = typer.Argument(..., help="视频 ID"),
):
    """获取视频详情（含分段、笔记、学习进度）"""
    _out(get_client().videos_get(video_id))


@app.command("process")
def videos_process(
    video_id: int = typer.Argument(..., help="视频 ID"),
):
    """触发视频处理（音频提取 + ASR + 分段分析）"""
    _out(get_client().videos_process(video_id))


# ═══════════════════════════════════════════════════════════════════════════
# 分段管理
# ═══════════════════════════════════════════════════════════════════════════

seg_app = typer.Typer(help="视频分段管理")
app.add_typer(seg_app, name="segments")


@seg_app.command("add")
def seg_add(
    video_id: int = typer.Argument(..., help="视频 ID"),
    title: str = typer.Argument(..., help="分段标题"),
    start: int = typer.Argument(..., help="开始时间（秒）"),
    end: int = typer.Argument(..., help="结束时间（秒）"),
    seg_type: str = typer.Option("qa", "--type", help="分段类型: qa/intro/practice"),
    transcription: Optional[str] = typer.Option(None, "--transcription", help="转录文本"),
):
    """手动添加视频分段"""
    _out(get_client().videos_add_segment(
        video_id, title=title, start_time=start, end_time=end,
        segment_type=seg_type, transcription=transcription,
    ))


@seg_app.command("update")
def seg_update(
    segment_id: int = typer.Argument(..., help="分段 ID"),
    title: Optional[str] = typer.Option(None, "--title", help="新标题"),
    start: Optional[int] = typer.Option(None, "--start", help="新开始时间"),
    end: Optional[int] = typer.Option(None, "--end", help="新结束时间"),
):
    """更新分段信息"""
    _out(get_client().videos_update_segment(segment_id, title=title, start_time=start, end_time=end))


@seg_app.command("delete")
def seg_delete(
    segment_id: int = typer.Argument(..., help="分段 ID"),
):
    """删除分段"""
    _out(get_client().videos_delete_segment(segment_id))


# ═══════════════════════════════════════════════════════════════════════════
# 笔记
# ═══════════════════════════════════════════════════════════════════════════

@app.command("note")
def videos_note(
    segment_id: int = typer.Argument(..., help="分段 ID"),
    content: str = typer.Argument(..., help="笔记内容（Markdown）"),
):
    """添加或更新分段笔记"""
    _out(get_client().videos_add_note(segment_id, content=content))


# ═══════════════════════════════════════════════════════════════════════════
# 学习进度
# ═══════════════════════════════════════════════════════════════════════════

@app.command("progress")
def videos_progress(
    segment_id: int = typer.Argument(..., help="分段 ID"),
    mastered: Optional[int] = typer.Option(None, "--mastered", help="是否已掌握: 0=否 1=是"),
    loop_count: Optional[int] = typer.Option(None, "--loops", help="循环练习次数"),
):
    """更新学习进度"""
    _out(get_client().videos_update_progress(segment_id, mastered=mastered, loop_count=loop_count))
