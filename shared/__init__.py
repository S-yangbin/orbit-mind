"""共享模块"""
from .message_protocol import (
    CommandMessage,
    ResultMessage,
    parse_message,
    is_command_message,
    is_result_message,
)

__all__ = [
    "CommandMessage",
    "ResultMessage",
    "parse_message",
    "is_command_message",
    "is_result_message",
]
