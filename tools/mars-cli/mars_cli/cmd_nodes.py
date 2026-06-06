"""节点管理命令组: nodes list/delete + exec 远程命令"""

import json
import sys

import typer
from rich.console import Console
from rich.table import Table

from .context import get_client

app = typer.Typer(help="home-agent 节点管理与远程命令执行")
console = Console()


def _out(data):
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


@app.command("list")
def nodes_list(
    stale: int = typer.Option(180, "--stale", help="心跳超时阈值（秒），超过此时间未心跳视为离线"),
    table: bool = typer.Option(False, "--table", help="以表格形式展示"),
):
    """列出所有已注册的 home-agent 节点及在线状态"""
    data = get_client().list_nodes(stale=stale)
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
                node["node_id"], node.get("hostname", ""), node.get("ip", ""),
                node.get("platform", ""), status_str, node.get("uptime", ""),
                str(node.get("last_heartbeat_at", ""))[:19] if node.get("last_heartbeat_at") else "-",
            )
        console.print(t)
    else:
        _out(data)


@app.command("delete")
def nodes_delete(
    node_id: str = typer.Argument(..., help="要删除的节点 ID"),
):
    """删除指定节点（仅删除注册记录，不影响远程 agent）"""
    _out(get_client().delete_node(node_id))


@app.command("exec")
def nodes_exec(
    node_id: str = typer.Argument(..., help="目标节点 ID（必须在线）"),
    command: str = typer.Argument(..., help="要执行的 shell 命令（建议用单引号包裹）"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="超时秒数，默认 30"),
):
    """在远程节点执行 shell 命令并返回结果

    命令通过 WebSocket 转发到目标节点的 home-agent 执行。
    节点会进行安全策略校验，危险命令会被拦截。
    CLI 退出码与远程命令的 exit_code 一致。
    """
    result = get_client().execute_command(node_id=node_id, command=command, timeout=timeout)
    _out(result)
    raise typer.Exit(code=result.get("exit_code", 1))
