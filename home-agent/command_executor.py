"""
命令执行引擎
使用 subprocess 执行 shell 命令，支持超时保护
"""

import logging
import subprocess
import time
from typing import Optional

from shared.message_protocol import ResultMessage

logger = logging.getLogger(__name__)


def execute_command(
    command: str,
    timeout: int = 30,
    working_dir: Optional[str] = None,
    max_timeout: int = 120,
) -> ResultMessage:
    """
    执行 shell 命令并返回结果
    
    Args:
        command: shell 命令字符串
        timeout: 命令超时时间（秒）
        working_dir: 工作目录
        max_timeout: 最大允许超时（秒）
        
    Returns:
        ResultMessage 对象
    """
    request_id = ""  # 由调用方设置
    
    # 限制超时时间
    effective_timeout = min(timeout, max_timeout)
    
    logger.info(
        "执行命令: %s (timeout=%ds, cwd=%s)",
        command, effective_timeout, working_dir
    )
    
    start_time = time.time()
    
    try:
        # 使用 bash -il (交互式 + 登录 shell) 执行，同时加载 .bashrc 和 .profile / .bash_profile
        result = subprocess.run(
            ["/bin/bash", "-il", "-c", command],
            capture_output=True,
            text=True,
            timeout=effective_timeout,
            cwd=working_dir,
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "命令执行完成: exit_code=%d, duration=%dms",
            result.returncode, duration_ms
        )
        
        return ResultMessage(
            request_id=request_id,
            exit_code=result.returncode,
            stdout=result.stdout[-64000:] if result.stdout else "",  # 截断过长输出
            stderr=result.stderr[-16000:] if result.stderr else "",
            duration_ms=duration_ms,
        )
        
    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.warning("命令执行超时 (%ds): %s", effective_timeout, command)
        return ResultMessage(
            request_id=request_id,
            exit_code=-1,
            stdout="",
            stderr=f"命令执行超时 ({effective_timeout}s)",
            duration_ms=duration_ms,
        )
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error("命令执行异常: %s, error=%s", command, str(e))
        return ResultMessage(
            request_id=request_id,
            exit_code=-2,
            stdout="",
            stderr=f"执行异常: {str(e)}",
            duration_ms=duration_ms,
        )
