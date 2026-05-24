"""
命令审计日志模块
持久化记录所有命令的执行情况，用于安全审计和问题排查
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """命令审计日志记录器"""

    def __init__(self, log_dir: Optional[str] = None):
        """
        初始化审计日志

        Args:
            log_dir: 审计日志目录，默认 ~/orbit-mind/logs/
        """
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / "orbit-mind" / "logs"

        self.log_dir.mkdir(parents=True, exist_ok=True)
        logger.info("审计日志目录: %s", self.log_dir)

    def _get_log_file(self) -> Path:
        """获取当天的日志文件路径"""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"commands-{date_str}.jsonl"

    def log_command(
        self,
        request_id: str,
        command: str,
        exit_code: int,
        duration_ms: int,
        blocked: bool = False,
        block_reason: str = "",
        stdout_preview: str = "",
        stderr_preview: str = "",
    ) -> None:
        """
        记录一条命令执行日志

        Args:
            request_id: 请求 ID
            command: 执行的命令
            exit_code: 退出码
            duration_ms: 执行耗时（毫秒）
            blocked: 是否被安全策略拦截
            block_reason: 拦截原因
            stdout_preview: stdout 前 500 字符预览
            stderr_preview: stderr 前 500 字符预览
        """
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "command": command,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "blocked": blocked,
            "block_reason": block_reason,
            "stdout_preview": stdout_preview[:500],
            "stderr_preview": stderr_preview[:500],
            "status": "blocked" if blocked else ("success" if exit_code == 0 else "failed"),
        }

        try:
            log_file = self._get_log_file()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.debug("审计日志已写入: %s, request_id=%s", log_file.name, request_id)
        except Exception as e:
            logger.error("审计日志写入失败: %s", str(e))


class NullAuditLogger:
    """空审计日志记录器（禁用审计时使用）"""

    def log_command(self, *args, **kwargs) -> None:
        pass
