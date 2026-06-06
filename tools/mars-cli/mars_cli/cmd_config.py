"""mars-cli config 子命令 —— 管理 CLI 配置文件

支持查看、设置、删除配置项，以及初始化配置文件。
配置文件默认写入 ~/.config/mars-cli/config.json，也可通过 --config-path 全局选项指定。
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    help="管理 mars-cli 配置文件（查看、设置、删除配置项）。",
    add_completion=False,
    no_args_is_help=True,
)

# 合法的配置键名
_VALID_KEYS = {"url", "api_key", "username", "password", "default_node", "default_timeout"}

# 配置文件默认路径
_DEFAULT_CONFIG_PATH = Path.home() / ".config" / "mars-cli" / "config.json"


def _resolve_config_path(config_path: Optional[str] = None) -> Path:
    """解析配置文件路径，优先使用显式指定路径，否则用默认路径。"""
    if config_path:
        return Path(config_path).expanduser().resolve()
    return _DEFAULT_CONFIG_PATH


def _load_config(path: Path) -> dict:
    """加载配置文件，不存在则返回空 dict。"""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: 配置文件 JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)


def _save_config(path: Path, cfg: dict):
    """保存配置到 JSON 文件，自动创建目录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ─── show: 显示当前配置 ────────────────────────────────────────────────────

@app.command(help="显示当前配置文件内容和路径。")
def show(
    config_path: Optional[str] = typer.Option(
        None, "--config-path", help="指定配置文件路径（默认 ~/.config/mars-cli/config.json）。",
    ),
):
    path = _resolve_config_path(config_path)
    cfg = _load_config(path)
    typer.echo(f"配置文件: {path}")
    if not cfg:
        typer.echo("（配置文件不存在或为空）")
    else:
        # 对敏感字段脱敏显示
        display = {}
        for k, v in cfg.items():
            if k in ("api_key", "password") and v and len(str(v)) > 4:
                s = str(v)
                display[k] = s[:2] + "***" + s[-2:]
            else:
                display[k] = v
        typer.echo(json.dumps(display, ensure_ascii=False, indent=2))


# ─── set: 设置配置项 ────────────────────────────────────────────────────────

@app.command(name="set", help="设置一个配置项的值。")
def set_value(
    key: str = typer.Argument(help=f"配置项名称，可选: {', '.join(sorted(_VALID_KEYS))}"),
    value: str = typer.Argument(help="配置项的值。"),
    config_path: Optional[str] = typer.Option(
        None, "--config-path", help="指定配置文件路径。",
    ),
):
    if key not in _VALID_KEYS:
        typer.echo(f"ERROR: 无效的配置项 '{key}'。可选: {', '.join(sorted(_VALID_KEYS))}", err=True)
        raise typer.Exit(1)

    # default_timeout 应为整数
    if key == "default_timeout":
        try:
            value = int(value)  # type: ignore[assignment]
        except ValueError:
            typer.echo("ERROR: default_timeout 必须是整数。", err=True)
            raise typer.Exit(1)

    path = _resolve_config_path(config_path)
    cfg = _load_config(path)
    cfg[key] = value
    _save_config(path, cfg)
    typer.echo(f"已设置 {key} = {value}")
    typer.echo(f"配置文件: {path}")


# ─── get: 获取单个配置项 ────────────────────────────────────────────────────

@app.command(help="获取一个配置项的值。")
def get(
    key: str = typer.Argument(help=f"配置项名称，可选: {', '.join(sorted(_VALID_KEYS))}"),
    config_path: Optional[str] = typer.Option(
        None, "--config-path", help="指定配置文件路径。",
    ),
):
    if key not in _VALID_KEYS:
        typer.echo(f"ERROR: 无效的配置项 '{key}'。可选: {', '.join(sorted(_VALID_KEYS))}", err=True)
        raise typer.Exit(1)

    path = _resolve_config_path(config_path)
    cfg = _load_config(path)
    val = cfg.get(key)
    if val is None:
        typer.echo(f"未设置 {key}")
        raise typer.Exit(1)
    typer.echo(val)


# ─── delete: 删除配置项 ─────────────────────────────────────────────────────

@app.command(help="删除一个配置项。")
def delete(
    key: str = typer.Argument(help=f"配置项名称，可选: {', '.join(sorted(_VALID_KEYS))}"),
    config_path: Optional[str] = typer.Option(
        None, "--config-path", help="指定配置文件路径。",
    ),
):
    if key not in _VALID_KEYS:
        typer.echo(f"ERROR: 无效的配置项 '{key}'。可选: {', '.join(sorted(_VALID_KEYS))}", err=True)
        raise typer.Exit(1)

    path = _resolve_config_path(config_path)
    cfg = _load_config(path)
    if key not in cfg:
        typer.echo(f"配置项 {key} 不存在，无需删除。")
        return
    del cfg[key]
    _save_config(path, cfg)
    typer.echo(f"已删除 {key}")
    typer.echo(f"配置文件: {path}")


# ─── init: 初始化配置文件 ───────────────────────────────────────────────────

@app.command(help="交互式初始化配置文件（逐步输入各配置项）。")
def init(
    config_path: Optional[str] = typer.Option(
        None, "--config-path", help="指定配置文件路径。",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已有配置文件。"),
):
    path = _resolve_config_path(config_path)

    if path.exists() and not force:
        typer.echo(f"配置文件已存在: {path}")
        typer.echo("如需重新初始化，请使用 --force 参数。")
        raise typer.Exit(1)

    typer.echo("mars-cli 配置文件初始化")
    typer.echo(f"配置文件路径: {path}")
    typer.echo("（直接回车跳过可选项）\n")

    cfg = {}

    url = typer.prompt("服务地址 (url)", default="")
    if url:
        cfg["url"] = url.rstrip("/")

    api_key = typer.prompt("API Key (api_key)", default="")
    if api_key:
        cfg["api_key"] = api_key

    username = typer.prompt("用户名 (username)", default="")
    if username:
        cfg["username"] = username

    password = typer.prompt("密码 (password)", default="", hide_input=True)
    if password:
        cfg["password"] = password

    default_node = typer.prompt("默认节点 (default_node)", default="")
    if default_node:
        cfg["default_node"] = default_node

    default_timeout = typer.prompt("默认超时秒数 (default_timeout)", default="30")
    try:
        cfg["default_timeout"] = int(default_timeout)
    except ValueError:
        cfg["default_timeout"] = 30

    _save_config(path, cfg)
    typer.echo(f"\n配置已保存到: {path}")
    typer.echo(json.dumps(cfg, ensure_ascii=False, indent=2))


# ─── path: 显示配置文件路径 ─────────────────────────────────────────────────

@app.command(help="显示配置文件路径。")
def path(
    config_path: Optional[str] = typer.Option(
        None, "--config-path", help="指定配置文件路径。",
    ),
):
    p = _resolve_config_path(config_path)
    typer.echo(str(p))
    if p.exists():
        typer.echo("（文件存在）")
    else:
        typer.echo("（文件不存在）")
