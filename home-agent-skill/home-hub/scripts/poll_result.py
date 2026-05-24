#!/usr/bin/env python3
"""
poll_result.py - 轮询 MNS 队列获取命令执行结果
从 MNS 队列中查找匹配 request_id 的 result 消息

用法: python poll_result.py <request_id> [--max-wait 60]
输出: JSON 格式的执行结果
"""

import argparse
import json
import os
import sys
import time

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
    parser = argparse.ArgumentParser(description="轮询命令执行结果")
    parser.add_argument("request_id", help="命令的 request_id")
    parser.add_argument("--max-wait", type=int, default=60, help="最大等待时间（秒），默认 60")
    args = parser.parse_args()

    # 读取环境变量
    endpoint = get_env("MNS_ENDPOINT")
    access_key_id = get_env("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = get_env("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    queue_name = get_env("MNS_QUEUE_NAME")

    # 初始化 MNS
    try:
        account = Account(endpoint, access_key_id, access_key_secret, "")
        queue = account.get_queue(queue_name)
        queue.set_encoding(False)
    except Exception as e:
        print(f"ERROR: MNS 初始化失败 - {e}", file=sys.stderr)
        sys.exit(1)

    start_time = time.time()
    # 每次长轮询等待时间，剩余不足 5 秒时用剩余时间
    poll_interval = 10

    while True:
        elapsed = time.time() - start_time
        remaining = args.max_wait - elapsed

        if remaining <= 0:
            print(
                json.dumps({
                    "error": "poll_timeout",
                    "message": f"等待超时（{args.max_wait}s），未收到执行结果",
                    "request_id": args.request_id,
                }, ensure_ascii=False)
            )
            sys.exit(0)

        wait_seconds = min(poll_interval, max(int(remaining), 1))

        try:
            recv_msg = queue.receive_message_with_str_body(wait_seconds)
        except MNSExceptionBase as e:
            if hasattr(e, "type") and e.type == "MessageNotExist":
                # 队列空，继续轮询
                continue
            print(f"ERROR: 接收消息失败 - {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            time.sleep(2)
            continue

        receipt_handle = recv_msg.receipt_handle
        message_body = recv_msg.message_body

        # 解析消息
        try:
            data = json.loads(message_body)
        except json.JSONDecodeError:
            # 无法解析的消息，删除后继续
            try:
                queue.delete_message(receipt_handle)
            except Exception:
                pass
            continue

        msg_type = data.get("type")
        msg_request_id = data.get("request_id")

        if msg_type == "result" and msg_request_id == args.request_id:
            # 找到匹配的结果消息，删除并输出
            try:
                queue.delete_message(receipt_handle)
            except Exception:
                pass
            print(json.dumps(data, ensure_ascii=False, indent=2))
            sys.exit(0)

        else:
            # 非目标消息：re-send 回队列后删除原消息
            try:
                new_msg = Message(message_body)
                queue.send_message(new_msg)
                queue.delete_message(receipt_handle)
            except Exception as e:
                # re-send 失败时至少不要删除原消息
                print(f"WARNING: re-send 消息失败 - {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
