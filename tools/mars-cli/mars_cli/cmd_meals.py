"""餐饮管理命令组: meals members/dishes/plan/history/preferences"""

import json
from typing import Optional

import typer

from .context import get_client

app = typer.Typer(help="餐饮计划与用餐记录管理")


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


# ═══════════════════════════════════════════════════════════════════════════
# 家庭成员
# ═══════════════════════════════════════════════════════════════════════════

members_app = typer.Typer(help="家庭成员管理")
app.add_typer(members_app, name="members")


@members_app.command("list")
def members_list():
    """列出所有家庭成员"""
    _out(get_client().meals_list_members())


@members_app.command("add")
def members_add(
    name: str = typer.Argument(..., help="成员名称"),
    avatar: str = typer.Option("🧑", "--avatar", help="头像 emoji"),
    board_color: Optional[str] = typer.Option(None, "--color", help="留言板颜色 (hex)"),
):
    """添加家庭成员"""
    _out(get_client().meals_create_member(name=name, avatar=avatar, board_color=board_color))


@members_app.command("update")
def members_update(
    member_id: int = typer.Argument(..., help="成员 ID"),
    name: Optional[str] = typer.Option(None, "--name", help="新名称"),
    avatar: Optional[str] = typer.Option(None, "--avatar", help="新头像"),
):
    """更新家庭成员信息"""
    _out(get_client().meals_update_member(member_id, name=name, avatar=avatar))


@members_app.command("delete")
def members_delete(
    member_id: int = typer.Argument(..., help="成员 ID"),
):
    """删除家庭成员"""
    _out(get_client().meals_delete_member(member_id))


# ═══════════════════════════════════════════════════════════════════════════
# 菜品
# ═══════════════════════════════════════════════════════════════════════════

dishes_app = typer.Typer(help="菜品库管理")
app.add_typer(dishes_app, name="dishes")


@dishes_app.command("list")
def dishes_list(
    keyword: Optional[str] = typer.Option(None, "-q", "--keyword", help="搜索关键词"),
    category: Optional[str] = typer.Option(None, "--category", help="按分类过滤"),
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", help="每页数量"),
):
    """查询菜品列表"""
    _out(get_client().meals_list_dishes(page=page, page_size=page_size, keyword=keyword, category=category))


@dishes_app.command("get")
def dishes_get(
    dish_id: int = typer.Argument(..., help="菜品 ID"),
):
    """获取菜品详情"""
    _out(get_client().meals_get_dish(dish_id))


@dishes_app.command("add")
def dishes_add(
    name: str = typer.Argument(..., help="菜品名称"),
    category: str = typer.Option("荤菜", "--category", "-c", help="分类"),
    recipe: Optional[str] = typer.Option(None, "--recipe", help="做法"),
):
    """添加新菜品"""
    _out(get_client().meals_create_dish(name=name, category=category, recipe=recipe))


# ═══════════════════════════════════════════════════════════════════════════
# 菜单计划
# ═══════════════════════════════════════════════════════════════════════════

plan_app = typer.Typer(help="周末菜单计划管理")
app.add_typer(plan_app, name="plan")


@plan_app.command("current")
def plan_current():
    """查看当前菜单（前4周+后4周，含实际用餐记录）"""
    _out(get_client().meals_current_plan())


@plan_app.command("generate")
def plan_generate(
    week_start: Optional[str] = typer.Option(None, "--week-start", help="起始周 YYYY-MM-DD（默认今天）"),
):
    """AI 生成月度周末菜单（耗时较长，请耐心等待）"""
    _out(get_client().meals_generate_plan(week_start_date=week_start))


@plan_app.command("confirm")
def plan_confirm():
    """确认本周菜单"""
    _out(get_client().meals_confirm_plan())


@plan_app.command("add")
def plan_add(
    date: str = typer.Argument(..., help="日期 YYYY-MM-DD"),
    meal_type: str = typer.Argument(..., help="餐次: breakfast/lunch/dinner"),
    dish_id: int = typer.Argument(..., help="菜品 ID"),
):
    """手动添加菜品到本周菜单"""
    _out(get_client().meals_add_plan_item(date=date, meal_type=meal_type, dish_id=dish_id))


@plan_app.command("replace")
def plan_replace(
    item_id: int = typer.Argument(..., help="菜单项 ID"),
    dish_id: int = typer.Argument(..., help="替换为菜品 ID"),
):
    """替换菜单中的菜品"""
    _out(get_client().meals_replace_plan_item(item_id=item_id, dish_id=dish_id))


@plan_app.command("remove")
def plan_remove(
    item_id: int = typer.Argument(..., help="菜单项 ID"),
):
    """移除菜单项"""
    _out(get_client().meals_remove_plan_item(item_id))


# ═══════════════════════════════════════════════════════════════════════════
# 用餐记录
# ═══════════════════════════════════════════════════════════════════════════

history_app = typer.Typer(help="用餐记录与统计")
app.add_typer(history_app, name="history")


@history_app.command("list")
def history_list(
    page: int = typer.Option(1, "--page", help="页码"),
    page_size: int = typer.Option(20, "--page-size", help="每页数量"),
    start_date: Optional[str] = typer.Option(None, "--start", help="起始日期 YYYY-MM-DD"),
    end_date: Optional[str] = typer.Option(None, "--end", help="结束日期 YYYY-MM-DD"),
):
    """查询用餐记录列表"""
    _out(get_client().meals_list_logs(page=page, page_size=page_size, start_date=start_date, end_date=end_date))


@history_app.command("stats")
def history_stats(
    days: int = typer.Option(14, "--days", help="统计天数范围"),
):
    """获取用餐统计（菜品频次、重复率等）"""
    _out(get_client().meals_history_stats(days=days))


@history_app.command("add")
def history_add(
    date: str = typer.Argument(..., help="日期 YYYY-MM-DD"),
    meal_type: str = typer.Argument(..., help="餐次: breakfast/lunch/dinner"),
    dishes: str = typer.Argument(..., help='菜品 JSON，如 \'[{"name":"红烧肉"},{"dish_id":5,"name":"青菜"}]\''),
    image_path: str = typer.Option("", "--image", help="照片路径"),
    rating: Optional[int] = typer.Option(None, "--rating", help="评分 1-5"),
    note: Optional[str] = typer.Option(None, "--note", help="备注"),
):
    """创建用餐记录"""
    import json as _json
    try:
        dish_list = _json.loads(dishes)
    except _json.JSONDecodeError as e:
        typer.echo(f"ERROR: 菜品 JSON 解析失败: {e}", err=True)
        raise typer.Exit(code=1)
    _out(get_client().meals_create_log(
        date=date, meal_type=meal_type, dishes=dish_list,
        image_path=image_path, rating=rating, note=note,
    ))


# ═══════════════════════════════════════════════════════════════════════════
# 偏好
# ═══════════════════════════════════════════════════════════════════════════

pref_app = typer.Typer(help="菜品偏好查询")
app.add_typer(pref_app, name="preferences")


@pref_app.command("list")
def pref_list():
    """查看所有成员的菜品偏好"""
    _out(get_client().meals_preferences())


@pref_app.command("dish")
def pref_dish(
    dish_id: int = typer.Argument(..., help="菜品 ID"),
):
    """查看谁喜欢某道菜"""
    _out(get_client().meals_dish_liked_by(dish_id))
