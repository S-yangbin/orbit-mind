#!/usr/bin/env python3
"""
send_command.py - 发送命令到家庭服务器 (WebSocket 架构)
通过 mars-sandbox HTTP API 发送命令,由 home-agent 通过 WebSocket 接收并执行

用法: python send_command.py <node_id> "your_command" [--timeout 30]
输出: JSON 格式的执行结果
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
    parser = argparse.ArgumentParser(description="发送命令到家庭服务器")
    parser.add_argument("node_id", help="目标节点 ID")
    parser.add_argument("command", help="要执行的 shell 命令")
    parser.add_argument("--timeout", type=int, default=30, help="命令执行超时时间（秒），默认 30")
    args = parser.parse_args()

    # 读取环境变量
    mars_sandbox_url = get_env("MARS_SANDBOX_URL").rstrip("/")
    api_key = get_env("MARS_SANDBOX_API_KEY")

    # 构建请求
    payload = {
        "node_id": args.node_id,
        "command": args.command,
        "timeout": args.timeout,
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }

    # 发送命令到 mars-sandbox
    try:
        print(f"正在发送命令到节点 {args.node_id}...")
        resp = requests.post(
            f"{mars_sandbox_url}/api/commands",
            json=payload,
            headers=headers,
            timeout=args.timeout + 10,  # 额外 10 秒缓冲
        )
        resp.raise_for_status()
        
        # 获取执行结果
        result = resp.json()
        
        # 格式化输出
        print("\n" + "=" * 60)
        print(f"节点: {args.node_id}")
        print(f"命令: {args.command}")
        print(f"退出码: {result.get('exit_code', 'N/A')}")
        print(f"耗时: {result.get('duration_ms', 0)}ms")
        print("=" * 60)
        
        if result.get('stdout'):
            print("\n[标准输出]")
            print(result['stdout'])
        
        if result.get('stderr'):
            print("\n[标准错误]")
            print(result['stderr'], file=sys.stderr)
        
        # 返回退出码
        sys.exit(result.get('exit_code', 0))

    except requests.Timeout:
        print(f"ERROR: 请求超时（{args.timeout + 10}s）", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"ERROR: 请求失败 - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
