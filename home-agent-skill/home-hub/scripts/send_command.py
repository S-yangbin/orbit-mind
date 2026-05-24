#!/usr/bin/env python3
"""
send_command.py - 发送命令到家庭服务器
将命令消息发送到 MNS 队列，由 home-agent 消费执行

用法: python send_command.py "your_command" [--timeout 30]
输出: REQUEST_ID=<uuid>
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone

from mns.account import Account
from mns.queue import Message
from mns.mns_exception import MNSExceptionBase


def get_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"ERROR: 环境变量 {name} 未设置", file=sys.stderr)
        sys.exit(1)
    return value


def main():
    parser = argparse.ArgumentParser(description="发送命令到家庭服务器")
    parser.add_argument("command", help="要执行的 shell 命令")
    parser.add_argument("--timeout", type=int, default=30, help="命令执行超时时间（秒），默认 30")
    args = parser.parse_args()

    # 读取环境变量
    endpoint = get_env("MNS_ENDPOINT")
    access_key_id = get_env("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = get_env("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    queue_name = get_env("MNS_QUEUE_NAME")

    # 构建命令消息
    request_id = str(uuid.uuid4())
    message = {
        "request_id": request_id,
        "type": "command",
        "command": args.command,
        "timeout": args.timeout,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # 发送到 MNS 队列
    try:
        account = Account(endpoint, access_key_id, access_key_secret, "")
        queue = account.get_queue(queue_name)
        queue.set_encoding(False)

        msg = Message(json.dumps(message, ensure_ascii=False))
        result = queue.send_message(msg)

        # 输出 request_id（Agent 用此值轮询结果）
        print(f"REQUEST_ID={request_id}")

    except MNSExceptionBase as e:
        print(f"ERROR: 发送消息失败 - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
