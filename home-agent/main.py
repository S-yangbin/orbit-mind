"""
Home Agent 守护进程
长轮询 MNS 队列，接收命令消息并执行，将结果发回队列
"""

import json
import logging
import signal
import sys
import os
import argparse
from pathlib import Path

# 将项目根目录和 home-agent 目录加入 path
_project_root = str(Path(__file__).resolve().parent.parent)
_home_agent_dir = str(Path(__file__).resolve().parent)
sys.path.insert(0, _project_root)
sys.path.insert(0, _home_agent_dir)

from shared.message_protocol import (
    CommandMessage,
    ResultMessage,
    parse_message,
    is_command_message,
    is_result_message,
)
from config import load_config, validate_config
from mns_client import MNSClient
from command_executor import execute_command
from security import check_command
from command_logger import AuditLogger, NullAuditLogger

# 优雅退出标志
_running = True


def setup_logging(log_file: str = None):
    """配置日志，支持同时输出到 stdout 和文件"""
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = []

    # systemd 场景下始终输出到 stdout（journalctl 采集）
    handlers.append(logging.StreamHandler(sys.stdout))

    # 如果配置了文件，同时写入文件
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(str(log_path), encoding="utf-8"))

    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=handlers,
    )


def signal_handler(signum, frame):
    """信号处理：优雅退出"""
    global _running
    logging.getLogger(__name__).info("收到信号 %s，准备退出...", signum)
    _running = False


def process_message(mns_client: MNSClient, receipt_handle: str, message_body: str, config, audit_logger):
    """
    处理收到的消息

    单队列模式：
    - command 消息 -> 执行命令，发送 result，删除原消息
    - result 消息 -> re-send 回队列，删除原消息（这不是给 home-agent 的）
    """
    logger = logging.getLogger(__name__)
    
    try:
        data = parse_message(message_body)
    except json.JSONDecodeError as e:
        logger.error("消息 JSON 解析失败: %s, body=%s", str(e), message_body[:200])
        # 删除无法解析的消息，避免死循环
        try:
            mns_client.delete_message(receipt_handle)
        except Exception:
            pass
        return
    
    if is_command_message(data):
        _handle_command(mns_client, receipt_handle, data, config, audit_logger)
    elif is_result_message(data):
        _handle_result_passthrough(mns_client, receipt_handle, message_body, data)
    else:
        logger.warning("未知消息类型: %s, 删除消息", data.get("type"))
        try:
            mns_client.delete_message(receipt_handle)
        except Exception:
            pass


def _handle_command(mns_client: MNSClient, receipt_handle: str, data: dict, config, audit_logger):
    """处理命令消息"""
    logger = logging.getLogger(__name__)
    
    try:
        cmd_msg = CommandMessage.from_dict(data)
    except Exception as e:
        logger.error("命令消息解析失败: %s", str(e))
        mns_client.delete_message(receipt_handle)
        return
    
    request_id = cmd_msg.request_id
    command = cmd_msg.command
    timeout = min(cmd_msg.timeout, config.agent.max_timeout)
    
    logger.info(
        "收到命令: request_id=%s, command=%s, timeout=%ds",
        request_id, command, timeout,
    )
    
    # 安全校验
    allowed, reason = check_command(
        command,
        config.agent.blocked_commands,
        config.agent.allowed_commands,
    )
    
    if not allowed:
        logger.warning("命令被拒绝: request_id=%s, reason=%s", request_id, reason)
        result = ResultMessage(
            request_id=request_id,
            exit_code=-100,
            stdout="",
            stderr=f"命令被安全策略拒绝: {reason}",
            duration_ms=0,
        )
        # 记录审计日志（被拦截）
        audit_logger.log_command(
            request_id=request_id,
            command=command,
            exit_code=-100,
            duration_ms=0,
            blocked=True,
            block_reason=reason,
        )
    else:
        # 执行命令
        result = execute_command(
            command=command,
            timeout=timeout,
            working_dir=config.agent.working_dir,
            max_timeout=config.agent.max_timeout,
        )
        result.request_id = request_id
        # 记录审计日志
        audit_logger.log_command(
            request_id=request_id,
            command=command,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
            blocked=False,
            stdout_preview=result.stdout,
            stderr_preview=result.stderr,
        )
    
    # 发送结果到队列
    result_json = result.to_json()
    mns_client.send_message(result_json)
    logger.info(
        "结果已发送: request_id=%s, exit_code=%d, duration=%dms",
        request_id, result.exit_code, result.duration_ms,
    )
    
    # 删除原始命令消息
    mns_client.delete_message(receipt_handle)


def _handle_result_passthrough(
    mns_client: MNSClient,
    receipt_handle: str,
    message_body: str,
    data: dict,
):
    """处理非本端的 result 消息：re-send 回队列"""
    logger = logging.getLogger(__name__)
    request_id = data.get("request_id", "unknown")
    logger.debug(
        "收到 result 消息（非本端），re-send 回队列: request_id=%s", request_id
    )
    mns_client.resend_and_delete(receipt_handle, message_body)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="Home Agent - 家庭服务器守护进程")
    parser.add_argument(
        "-c", "--config",
        type=str,
        default=None,
        help="配置文件路径 (默认自动查找)",
    )
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 配置日志
    setup_logging(config.agent.log_file)
    logger = logging.getLogger(__name__)
    
    # 验证配置
    errors = validate_config(config)
    if errors:
        for err in errors:
            logger.error("配置错误: %s", err)
        sys.exit(1)
    
    # 初始化审计日志
    audit_logger = AuditLogger(config.agent.audit_log_dir)

    logger.info("=" * 50)
    logger.info("Home Agent 启动")
    logger.info("MNS 队列: %s", config.mns.queue_name)
    logger.info("工作目录: %s", config.agent.working_dir)
    logger.info("最大超时: %ds", config.agent.max_timeout)
    logger.info("黑名单命令数: %d", len(config.agent.blocked_commands))
    logger.info("白名单模式: %s", "启用" if config.agent.allowed_commands else "未启用")
    logger.info("=" * 50)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化 MNS 客户端
    try:
        mns_client = MNSClient(
            endpoint=config.mns.endpoint,
            access_key_id=config.mns.access_key_id,
            access_key_secret=config.mns.access_key_secret,
            queue_name=config.mns.queue_name,
        )
    except Exception as e:
        logger.error("MNS 客户端初始化失败: %s", str(e))
        sys.exit(1)
    
    # 主循环
    wait_seconds = 30  # 长轮询等待时间
    
    while _running:
        try:
            result = mns_client.receive_message(wait_seconds)
            
            if result is None:
                logger.debug("队列空，继续等待...")
                continue
            
            receipt_handle, message_body = result
            process_message(mns_client, receipt_handle, message_body, config, audit_logger)
            
        except KeyboardInterrupt:
            logger.info("收到 KeyboardInterrupt，退出...")
            break
        except Exception as e:
            logger.error("主循环异常: %s", str(e), exc_info=True)
            # 短暂休眠后重试，避免快速循环
            import time
            time.sleep(5)
    
    logger.info("Home Agent 已退出")


if __name__ == "__main__":
    main()
