#!/usr/bin/env python3
"""
EPD-nRF5 命令行工具 - 通过 BLE 控制电子墨水屏设备

基于 Typer 框架，支持 JSON 输出，方便大模型调用。
"""

import typer

from .commands import app


def main():
    try:
        app()
    except KeyboardInterrupt:
        typer.echo("\n已取消")
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
