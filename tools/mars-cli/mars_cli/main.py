"""mars-cli 命令行主入口

面向大模型和运维人员的 mars-sandbox HTTP API 客户端工具。
支持远程节点管理、命令执行、页面查询等操作。

配置方式（二选一）:
  1. 环境变量:
     export MARS_SANDBOX_URL=http://<your-server-ip>:<port>
     export MARS_SANDBOX_API_KEY=your-api-key
  2. 命令行参数（优先级更高）:
     mars-cli --url http://... --api-key xxx <command>
"""

import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from mars_cli.client import MarsClient

# ─── Typer App ─────────────────────────────────────────────────────────────

app = typer.Typer(
    name="mars-cli",
    help=(
        "mars-sandbox 命令行客户端 —— 管理远程 home-agent 节点并执行命令。\n\n"
        "本工具通过 mars-sandbox HTTP API 与家庭 AI 中枢通信，"
        "可对已注册的 home-agent 节点进行远程 shell 命令执行、状态查询等操作。\n\n"
        "使用前须配置环境变量 MARS_SANDBOX_URL（服务端地址）和 MARS_SANDBOX_API_KEY（认证密钥）。"
    ),
    epilog=(
        "常见使用示例:\n\n"
        "  mars-cli nodes                          # 查看所有节点及在线状态\n"
        "  mars-cli exec my-node 'df -h'           # 在 my-node 上执行命令\n"
        "  mars-cli exec my-node 'reboot' -t 10    # 重启节点，超时 10 秒\n"
        "  mars-cli health                         # 检查 mars-sandbox 服务状态\n"
        "  mars-cli pages -q 'home'                # 搜索页面\n"
    ),
    add_completion=False,
    no_args_is_help=True,
)

console = Console()
err_console = Console(stderr=True)

# ─── 全局选项 ──────────────────────────────────────────────────────────────

_url_opt: Optional[str] = None
_api_key_opt: Optional[str] = None


@app.callback()
def main(
    url: Optional[str] = typer.Option(
        None,
        "--url",
        envvar="MARS_SANDBOX_URL",
        help="mars-sandbox 服务端地址，如 http://<your-server-ip>:<port>。也可通过 MARS_SANDBOX_URL 环境变量设置。",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="MARS_SANDBOX_API_KEY",
        help="API 认证密钥（X-API-Key）。也可通过 MARS_SANDBOX_API_KEY 环境变量设置。",
    ),
):
    """mars-sandbox 命令行客户端，用于管理远程节点和执行命令。"""
    global _url_opt, _api_key_opt
    _url_opt = url
    _api_key_opt = api_key


def _client() -> MarsClient:
    """获取 MarsClient 实例（延迟初始化）"""
    return MarsClient(base_url=_url_opt, api_key=_api_key_opt)


def _output(data, as_json: bool = False, exit_code: int = 0):
    """统一输出结果"""
    if as_json:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    raise typer.Exit(code=exit_code)


# ─── nodes: 节点列表 ──────────────────────────────────────────────────────

@app.command(
    help=(
        "列出所有已注册的 home-agent 节点及其在线状态。\n\n"
        "每个节点显示: node_id（节点标识）、hostname（主机名）、ip（IP 地址）、"
        "platform（操作系统）、status（online/offline）、uptime（运行时长）、"
        "last_heartbeat_at（最后心跳时间）。\n\n"
        "节点通过 WebSocket 心跳保活，超过 --stale 秒未收到心跳则判定为 offline。\n\n"
        "输出格式:\n"
        "  total: 节点总数\n"
        "  online: 在线节点数\n"
        "  offline: 离线节点数\n"
        "  nodes: 节点详情列表"
    ),
    epilog=(
        "示例:\n\n"
        "  mars-cli nodes                   # 列出所有节点\n"
        "  mars-cli nodes --stale 60        # 60秒无心跳视为离线\n"
        "  mars-cli nodes --table           # 以表格形式展示\n"
    ),
)
def nodes(
    stale: int = typer.Option(
        180,
        "--stale",
        help="心跳超时阈值（秒），超过该时间未收到心跳的节点标记为 offline。最小值 30，默认 180。",
    ),
    table: bool = typer.Option(
        False,
        "--table",
        help="以表格形式展示节点列表，便于人工阅读。默认输出 JSON 格式（适合程序解析）。",
    ),
):
    """列出所有已注册的 home-agent 节点及其在线/离线状态。"""
    client = _client()
    data = client.list_nodes(stale=stale)

    if table:
        t = Table(title=f"节点列表 (在线: {data['online']}/{data['total']})")
        t.add_column("节点 ID", style="cyan", no_wrap=True)
        t.add_column("主机名")
        t.add_column("IP 地址")
        t.add_column("系统")
        t.add_column("状态", justify="center")
        t.add_column("运行时长", justify="right")
        t.add_column("最后心跳")

        for node in data["nodes"]:
            status_str = "[green]online[/green]" if node["status"] == "online" else "[red]offline[/red]"
            t.add_row(
                node["node_id"],
                node.get("hostname", ""),
                node.get("ip", ""),
                node.get("platform", ""),
                status_str,
                node.get("uptime", ""),
                str(node.get("last_heartbeat_at", ""))[:19] if node.get("last_heartbeat_at") else "-",
            )
        console.print(t)
    else:
        _output(data)


# ─── exec: 执行远程命令 ────────────────────────────────────────────────────

@app.command(
    name="exec",
    help=(
        "在指定远程节点上执行 shell 命令。\n\n"
        "命令通过 mars-sandbox WebSocket 通道转发到目标节点的 home-agent 执行，"
        "并同步等待结果返回。节点配置了安全策略（命令黑白名单），危险命令会被拦截拒绝。\n\n"
        "参数说明:\n"
        "  NODE_ID  - 目标节点标识，须与已注册节点 ID 完全匹配，节点必须在线\n"
        "  COMMAND  - 要在远程节点上执行的 shell 命令字符串，用引号包裹\n\n"
        "返回值:\n"
        "  request_id  - 本次请求唯一标识 UUID\n"
        "  exit_code   - 命令退出码，0=成功，非 0=失败（与 shell 一致）\n"
        "  stdout      - 命令标准输出内容\n"
        "  stderr      - 命令标准错误内容\n"
        "  duration_ms - 命令在节点上的实际执行耗时（毫秒）\n\n"
        "退出码:\n"
        "  CLI 自身的退出码与远程命令的 exit_code 一致，便于在脚本中判断执行结果。"
    ),
    epilog=(
        "示例:\n\n"
        "  mars-cli exec my-node 'ls -la /home'\n"
        "  mars-cli exec my-node 'df -h' --timeout 15\n"
        "  mars-cli exec my-node 'cat /etc/hostname'\n"
        "  mars-cli exec my-node 'systemctl status home-agent'\n"
        "  mars-cli exec my-node 'free -m && df -h' -t 60\n"
        "\n"
        "提示: 复杂命令建议用引号包裹，避免 shell 提前展开。"
    ),
)
def exec_cmd(
    node_id: str = typer.Argument(
        ...,
        help="目标节点 ID，必须是已注册且当前在线的 home-agent 节点。",
    ),
    command: str = typer.Argument(
        ...,
        help="要在远程节点上执行的 shell 命令字符串。建议用单引号包裹，防止本地 shell 提前展开变量。",
    ),
    timeout: int = typer.Option(
        30,
        "--timeout", "-t",
        help="命令执行超时时间（秒），默认 30。超过该时间未返回结果则中止。建议长耗时命令（如 apt upgrade）设为 300。",
    ),
):
    """在远程节点上执行 shell 命令并返回结果。"""
    client = _client()
    result = client.execute_command(
        node_id=node_id,
        command=command,
        timeout=timeout,
    )

    exit_code = result.get("exit_code", 1)

    # 结构化输出
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    raise typer.Exit(code=exit_code)


# ─── health: 服务健康检查 ──────────────────────────────────────────────────

@app.command(
    help=(
        "检查 mars-sandbox 服务端是否正常运行。\n\n"
        "调用 /health 端点，无需 API Key 即可访问。"
        "返回服务状态信息，可用于监控和探活。\n\n"
        "适用场景:\n"
        "  - 执行命令前预先检查服务连通性\n"
        "  - 监控系统定期探活\n"
        "  - 排查网络连接问题"
    ),
    epilog="示例:\n\n  mars-cli health\n",
)
def health():
    """检查 mars-sandbox 服务运行状态（无需认证）。"""
    client = _client()
    data = client.health_check()
    _output(data)


# ─── pages: 页面管理 ───────────────────────────────────────────────────────

@app.command(
    help=(
        "查询 mars-sandbox 中托管的页面列表，支持关键词搜索、标签过滤和分页。\n\n"
        "页面是 mars-sandbox 管理的静态内容资源（如文档、项目展示页等）。\n\n"
        "输出字段:\n"
        "  total     - 符合条件的总数\n"
        "  page      - 当前页码\n"
        "  page_size - 每页数量\n"
        "  items     - 页面列表，每项包含 id/slug/title/description/tags 等"
    ),
    epilog=(
        "示例:\n\n"
        "  mars-cli pages                        # 列出前 20 条\n"
        "  mars-cli pages -q 'raspberry'         # 搜索包含 raspberry 的页面\n"
        "  mars-cli pages --tag iot --page 2     # 按标签过滤，第 2 页\n"
        "  mars-cli pages --category projects    # 按分类过滤\n"
    ),
)
def pages(
    q: Optional[str] = typer.Option(
        None, "--query", "-q",
        help="搜索关键词，匹配页面标题或描述，支持模糊搜索。",
    ),
    tag: Optional[str] = typer.Option(
        None, "--tag",
        help="按标签名称过滤，仅返回包含该标签的页面。",
    ),
    category: Optional[str] = typer.Option(
        None, "--category",
        help="按分类名称过滤页面。",
    ),
    page: int = typer.Option(
        1, "--page",
        help="页码，从 1 开始，默认第 1 页。",
    ),
    page_size: int = typer.Option(
        20, "--page-size",
        help="每页返回数量，默认 20，最大 100。",
    ),
):
    """查询 mars-sandbox 托管的页面列表（支持搜索和过滤）。"""
    client = _client()
    data = client.list_pages(q=q, tag=tag, category=category, page=page, page_size=page_size)
    _output(data)


@app.command(
    name="page",
    help=(
        "获取指定页面的详细信息。\n\n"
        "通过页面数据库 ID 查询，返回完整页面元数据，包括标题、描述、缩略图路径、"
        "入口文件、所属标签列表、创建和更新时间等。"
    ),
    epilog="示例:\n\n  mars-cli page 42\n",
)
def page_detail(
    page_id: int = typer.Argument(
        ...,
        help="页面数据库 ID（整数），可通过 mars-cli pages 列表获取。",
    ),
):
    """获取指定页面的详细信息。"""
    client = _client()
    data = client.get_page(page_id)
    _output(data)


# ─── tags: 标签列表 ────────────────────────────────────────────────────────

@app.command(
    help=(
        "列出 mars-sandbox 中所有标签及其关联页面数量。\n\n"
        "标签用于对页面进行分组和分类管理。\n\n"
        "输出格式为列表，每项包含:\n"
        "  id         - 标签数据库 ID\n"
        "  name       - 标签名称\n"
        "  page_count - 关联的页面数量"
    ),
    epilog="示例:\n\n  mars-cli tags\n",
)
def tags():
    """列出所有标签及关联页面数量。"""
    client = _client()
    data = client.list_tags()
    _output(data)


# ─── 入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
