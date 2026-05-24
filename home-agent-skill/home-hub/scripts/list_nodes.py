#!/usr/bin/env python3
"""
list_nodes.py - 查询当前在线的 home-agent 节点
通过调用 mars-sandbox API 获取节点列表

用法: python list_nodes.py [--stale 180]
输出: JSON 格式的在线节点列表
"""

import argparse
import json
import os
import sys

import requests


def get_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"ERROR: 环境变量 {name} 未设置", file=sys.stderr)
        sys.exit(1)
    return value


def main():
    parser = argparse.ArgumentParser(description="查询在线 home-agent 节点")
    parser.add_argument("--stale", type=int, default=180, help="超过多少秒视为离线（默认 180）")
    args = parser.parse_args()

    base_url = get_env("MARS_SANDBOX_URL").rstrip("/")
    api_key = get_env("MARS_SANDBOX_API_KEY")

    try:
        resp = requests.get(
            f"{base_url}/api/nodes",
            params={"stale": args.stale},
            headers={"X-API-Key": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except requests.RequestException as e:
        print(f"ERROR: 请求失败 - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
