"""
Home Agent 守护进程 (WebSocket 架构)
通过 WebSocket 连接 mars-sandbox,接收命令消息并执行,将结果发回
"""

import json
import logging
import signal
import sys
import os
import argparse
import asyncio
from pathlib import Path

# 将项目根目录和 home-agent 目录加入 path
_project_root = str(Path(__file__).resolve().parent.parent)
_home_agent_dir = str(Path(__file__).resolve().parent)
sys.path.insert(0, _project_root)
sys.path.insert(0, _home_agent_dir)

from shared.message_protocol import (
    CommandMessage,
    ResultMessage,
    ErrorMessage,
)
from config import load_config, validate_config
from ws_client import WebSocketClient
from command_executor import execute_command
from security import check_command
from command_logger import AuditLogger, NullAuditLogger


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


async def handle_command(ws_client: WebSocketClient, cmd_msg: CommandMessage, config, audit_logger) -> ResultMessage:
    """
    处理命令消息
    
    Args:
        ws_client: WebSocket 客户端
        cmd_msg: 命令消息
        config: 配置对象
        audit_logger: 审计日志
        
    Returns:
        执行结果消息
    """
    logger = logging.getLogger(__name__)
    
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
    
    logger.info(
        "命令执行完成: request_id=%s, exit_code=%d, duration=%dms",
        request_id, result.exit_code, result.duration_ms,
    )
    
    return result


async def async_main():
    """异步主入口"""
    parser = argparse.ArgumentParser(description="Home Agent - 家庭服务器守护进程 (WebSocket)")
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
    logger.info("Home Agent 启动 (WebSocket 架构)")
    logger.info("节点 ID: %s", config.agent.node_id)
    logger.info("mars-sandbox: %s", config.agent.mars_sandbox_url)
    logger.info("工作目录: %s", config.agent.working_dir)
    logger.info("最大超时: %ds", config.agent.max_timeout)
    logger.info("黑名单命令数: %d", len(config.agent.blocked_commands))
    logger.info("白名单模式: %s", "启用" if config.agent.allowed_commands else "未启用")
    logger.info("=" * 50)
    
    # 注册信号处理
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("收到退出信号，准备关闭...")
        stop_event.set()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    # 初始化 WebSocket 客户端
    ws_client = WebSocketClient(
        server_url=config.agent.mars_sandbox_url,
        node_id=config.agent.node_id,
        node_secret=config.agent.node_secret,
        heartbeat_interval=config.agent.heartbeat_interval,
        reconnect_delay=config.agent.reconnect_delay,
        max_reconnect_attempts=config.agent.max_reconnect_attempts,
    )
    
    # 设置命令处理器
    ws_client.set_command_handler(
        lambda cmd_msg: handle_command(ws_client, cmd_msg, config, audit_logger)
    )
    
    try:
        # 运行 WebSocket 客户端 (自动重连)
        await asyncio.gather(
            ws_client.run_with_reconnect(),
            stop_event.wait(),
        )
    except asyncio.CancelledError:
        logger.info("主循环被取消")
    finally:
        await ws_client.close()
        logger.info("Home Agent 已退出")


def main():
    """主入口"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("收到 KeyboardInterrupt，退出...")
    except Exception as e:
        logging.getLogger(__name__).error("启动失败: %s", str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
