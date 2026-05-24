"""
安全校验模块
命令黑白名单检查
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def check_command(
    command: str,
    blocked_commands: list,
    allowed_commands: list = None,
) -> Tuple[bool, str]:
    """
    校验命令是否允许执行
    
    Args:
        command: 待校验的命令字符串
        blocked_commands: 黑名单列表
        allowed_commands: 白名单列表，为空或 None 表示不限制
        
    Returns:
        (allowed, reason): 是否允许，原因说明
    """
    command_stripped = command.strip()
    
    # 白名单模式：如果配置了白名单，只允许白名单内的命令
    if allowed_commands:
        for prefix in allowed_commands:
            if command_stripped.startswith(prefix):
                logger.info("命令通过白名单校验: %s", command_stripped)
                return True, "白名单通过"
        return False, f"命令不在白名单内: {command_stripped}"
    
    # 黑名单检查
    for blocked in blocked_commands:
        blocked_stripped = blocked.strip()
        # 精确匹配或包含匹配
        if blocked_stripped in command_stripped or command_stripped.startswith(blocked_stripped):
            logger.warning("命令被黑名单拦截: %s (匹配: %s)", command_stripped, blocked_stripped)
            return False, f"命令被安全策略拦截 (匹配黑名单: {blocked_stripped})"
    
    logger.info("命令通过安全校验: %s", command_stripped)
    return True, "通过"
