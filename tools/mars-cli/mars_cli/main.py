"""mars-cli 命令行主入口

面向 AI Agent 和运维人员的 mars-sandbox HTTP API 全功能客户端工具。
支持远程节点管理、命令执行、留言板、餐饮计划、视频学习、云盘、
页面管理、标签、扫描等全部功能模块。

配置方式（三选一，优先级从高到低）:
  1. 命令行参数: mars-cli --url http://... --api-key xxx <command>
  2. 环境变量: MARS_SANDBOX_URL / MARS_SANDBOX_API_KEY / MARS_SANDBOX_USERNAME / MARS_SANDBOX_PASSWORD
  3. 配置文件: mars-cli.json (支持路径: ./mars-cli.json, ~/.config/mars-cli/config.json, ~/.mars-cli.json)

配置文件格式:
  {
    "url": "http://<server-ip>:<port>",
    "api_key": "your-api-key",
    "username": "admin",
    "password": "your-password",
    "default_node": "home-server-01",
    "default_timeout": 30
  }
"""

import json
import sys
from typing import Optional

import typer

from mars_cli.context import set_client
from mars_cli.client import MarsClient

from mars_cli import cmd_board
from mars_cli import cmd_meals
from mars_cli import cmd_nodes
from mars_cli import cmd_pages
from mars_cli import cmd_tags
from mars_cli import cmd_videos
from mars_cli import cmd_drive
from mars_cli import cmd_scan
from mars_cli import cmd_config
from mars_cli import cmd_dashboard
from mars_cli import cmd_schedule

# ─── Typer App ─────────────────────────────────────────────────────────────

app = typer.Typer(
    name="mars-cli",
    help=(
        "mars-sandbox 命令行客户端 —— AI Agent 友好的家庭中枢管理平台。\n\n"
        "支持功能模块: 节点管理(nodes) | 留言板(board) | 餐饮计划(meals) | "
        "视频学习(videos) | 云盘(drive) | 页面(pages) | 标签(tags) | 扫描(scan) | "
        "看板(dashboard) | 学习计划(schedule)\n\n"
        "使用前须配置连接信息（API Key 或 用户名+密码），详见 --help。"
    ),
    epilog=(
        "常见使用示例:\n\n"
        "  mars-cli nodes list                       # 查看所有节点\n"
        "  mars-cli nodes exec my-node 'df -h'       # 远程执行命令\n"
        "  mars-cli board list                       # 查看留言板\n"
        "  mars-cli board add '今晚不回家吃饭'        # 发布留言\n"
        "  mars-cli meals plan current               # 查看本周菜单\n"
        "  mars-cli meals plan generate              # AI 生成月度菜单\n"
        "  mars-cli meals members list               # 查看家庭成员\n"
        "  mars-cli videos list                      # 查看视频列表\n"
        "  mars-cli drive list                       # 查看云盘文件\n"
        "  mars-cli health                           # 检查服务状态\n"
        "  mars-cli dashboard refresh-wallpaper      # 刷新看板壁纸\n"
        "  mars-cli dashboard generate-wallpaper     # AI 生成高清壁纸\n"
        "  mars-cli dashboard list-wallpapers        # 列出已生成壁纸\n"
        "  mars-cli dashboard set-wallpaper <file>   # 设置指定壁纸\n"
        "  mars-cli schedule today                  # 查看今天的学习计划\n"
        "  mars-cli schedule complete <id> --note '...'  # 标记完成并备注\n"
    ),
    add_completion=False,
    no_args_is_help=True,
)

# ─── 全局选项 ──────────────────────────────────────────────────────────────

_url_opt: Optional[str] = None
_api_key_opt: Optional[str] = None
_username_opt: Optional[str] = None
_password_opt: Optional[str] = None


@app.callback()
def main(
    url: Optional[str] = typer.Option(
        None, "--url",
        envvar="MARS_SANDBOX_URL",
        help="mars-sandbox 服务地址。也可通过 MARS_SANDBOX_URL 环境变量或配置文件设置。",
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key",
        envvar="MARS_SANDBOX_API_KEY",
        help="API 认证密钥。也可通过 MARS_SANDBOX_API_KEY 环境变量或配置文件设置。",
    ),
    username: Optional[str] = typer.Option(
        None, "--username", "-u",
        envvar="MARS_SANDBOX_USERNAME",
        help="登录用户名（board/meals/videos 等接口需要）。也可通过环境变量或配置文件设置。",
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        envvar="MARS_SANDBOX_PASSWORD",
        help="登录密码。也可通过 MARS_SANDBOX_PASSWORD 环境变量或配置文件设置。",
    ),
):
    """mars-sandbox 全功能命令行客户端，面向 AI Agent 和运维人员。"""
    global _url_opt, _api_key_opt, _username_opt, _password_opt
    _url_opt = url
    _api_key_opt = api_key
    _username_opt = username
    _password_opt = password

    # config 子命令不需要连接服务器，跳过客户端初始化
    if len(sys.argv) > 1 and sys.argv[1] == "config":
        return

    client = MarsClient(
        base_url=_url_opt,
        api_key=_api_key_opt,
        username=_username_opt,
        password=_password_opt,
    )
    set_client(client)


# ─── 注册子命令组 ──────────────────────────────────────────────────────────

app.add_typer(cmd_nodes.app, name="nodes", help="节点管理与远程命令执行")
app.add_typer(cmd_board.app, name="board", help="家庭留言板管理")
app.add_typer(cmd_meals.app, name="meals", help="餐饮计划与用餐记录管理")
app.add_typer(cmd_pages.app, name="pages", help="托管页面管理")
app.add_typer(cmd_tags.app, name="tags", help="标签管理")
app.add_typer(cmd_videos.app, name="videos", help="视频学习管理（分段、笔记、进度）")
app.add_typer(cmd_drive.app, name="drive", help="云盘文件与文件夹管理")
app.add_typer(cmd_scan.app, name="scan", help="页面目录扫描")
app.add_typer(cmd_config.app, name="config", help="管理 CLI 配置文件")
app.add_typer(cmd_dashboard.app, name="dashboard", help="家庭看板管理（壁纸刷新等）")
app.add_typer(cmd_schedule.app, name="schedule", help="儿童学习计划管理（活动类型、周模板、每日计划）")


# ─── 顶层命令: 健康检查 ────────────────────────────────────────────────────

@app.command(
    help="检查 mars-sandbox 服务运行状态（无需认证）。",
    epilog="示例:\n\n  mars-cli health\n",
)
def health():
    """检查 mars-sandbox 服务运行状态（无需认证）。"""
    from mars_cli.context import get_client
    data = get_client().health_check()
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


# ─── 入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
