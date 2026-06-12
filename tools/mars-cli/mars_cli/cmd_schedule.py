"""学习计划管理命令组: schedule types/template/today/daily/add/complete/uncomplete/remove"""

import json
from typing import Optional

import typer

from .context import get_client

app = typer.Typer(help="儿童学习计划管理（活动类型、周模板、每日计划）")


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


# ═══════════════════════════════════════════════════════════════════════════
# 活动类型
# ═══════════════════════════════════════════════════════════════════════════

types_app = typer.Typer(help="活动类型管理")
app.add_typer(types_app, name="types")


@types_app.command("list")
def types_list():
    """列出所有活动类型"""
    _out(get_client().schedule_list_types())


@types_app.command("add")
def types_add(
    name: str = typer.Argument(..., help="活动名称，如'练钢琴'"),
    icon: str = typer.Option("📋", "--icon", help="emoji 图标"),
    color: str = typer.Option("#6b7280", "--color", help="显示颜色 hex"),
    category: str = typer.Option("custom", "--category", "-c", help="分类: homework/reading/sports/arts/freeplay/custom"),
):
    """新增自定义活动类型"""
    _out(get_client().schedule_create_type(name=name, icon=icon, color=color, category=category))


@types_app.command("update")
def types_update(
    type_id: int = typer.Argument(..., help="活动类型 ID"),
    name: Optional[str] = typer.Option(None, "--name", help="新名称"),
    icon: Optional[str] = typer.Option(None, "--icon", help="新图标"),
    color: Optional[str] = typer.Option(None, "--color", help="新颜色"),
):
    """更新活动类型名称/图标/颜色"""
    _out(get_client().schedule_update_type(type_id, name=name, icon=icon, color=color))


@types_app.command("delete")
def types_delete(
    type_id: int = typer.Argument(..., help="活动类型 ID（预设类型不可删）"),
):
    """删除自定义活动类型（预设不可删）"""
    _out(get_client().schedule_delete_type(type_id))


# ═══════════════════════════════════════════════════════════════════════════
# 周模板
# ═══════════════════════════════════════════════════════════════════════════

template_app = typer.Typer(help="周模板管理")
app.add_typer(template_app, name="template")


@template_app.command("get")
def template_get():
    """获取当前激活的周模板"""
    _out(get_client().schedule_get_template())


@template_app.command("set")
def template_set(
    template_json: str = typer.Argument(
        ...,
        help='周模板 JSON，如 \'{"name":"默认","days":{"mon":[1,3],"tue":[2,4],"wed":[1],"thu":[3,5],"fri":[1],"sat":[2,4,5],"sun":[5]}}\'',
    ),
):
    """设置周模板（JSON 格式，days 的 key 为 mon/tue/wed/thu/fri/sat/sun，value 为活动类型 ID 数组）"""
    try:
        data = json.loads(template_json)
    except json.JSONDecodeError as e:
        typer.echo(f"ERROR: JSON 解析失败: {e}", err=True)
        raise typer.Exit(code=1)
    name = data.get("name", "默认周计划")
    days = data.get("days", {})
    _out(get_client().schedule_set_template(name=name, days=days))


# ═══════════════════════════════════════════════════════════════════════════
# 每日计划
# ═══════════════════════════════════════════════════════════════════════════


@app.command("today")
def today():
    """查看今天的学习计划"""
    _out(get_client().schedule_today())


@app.command("daily")
def daily(
    date: str = typer.Argument(..., help="日期 YYYY-MM-DD"),
):
    """查看指定日期的学习计划"""
    _out(get_client().schedule_daily(date))


@app.command("add")
def add(
    date: str = typer.Argument(..., help="日期 YYYY-MM-DD"),
    activity_type_id: int = typer.Argument(..., help="活动类型 ID"),
):
    """手动添加活动到某天"""
    _out(get_client().schedule_add(date=date, activity_type_id=activity_type_id))


@app.command("complete")
def complete(
    item_id: int = typer.Argument(..., help="计划项 ID"),
    note: Optional[str] = typer.Option(None, "--note", "-n", help="完成备注"),
):
    """标记完成，可选附带完成备注"""
    _out(get_client().schedule_complete(item_id, note=note))


@app.command("uncomplete")
def uncomplete(
    item_id: int = typer.Argument(..., help="计划项 ID"),
):
    """取消完成标记"""
    _out(get_client().schedule_uncomplete(item_id))


@app.command("remove")
def remove(
    item_id: int = typer.Argument(..., help="计划项 ID"),
):
    """删除某天的活动"""
    _out(get_client().schedule_remove(item_id))
