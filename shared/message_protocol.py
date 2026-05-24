"""
消息协议定义 - 家庭 AI 中枢系统
定义命令消息和响应消息的标准格式
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
import json
import uuid


@dataclass
class CommandMessage:
    """命令消息（Hermes -> Home Agent）"""
    command: str
    request_id: str = None
    type: str = "command"
    timeout: int = 30  # 命令执行超时时间（秒）
    created_at: str = None
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(asdict(self), ensure_ascii=False)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CommandMessage':
        """从 JSON 字符串反序列化"""
        data = json.loads(json_str)
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CommandMessage':
        """从字典创建"""
        return cls(**data)


@dataclass
class ResultMessage:
    """响应消息（Home Agent -> Hermes）"""
    request_id: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    type: str = "result"
    duration_ms: int = 0
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(asdict(self), ensure_ascii=False)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ResultMessage':
        """从 JSON 字符串反序列化"""
        data = json.loads(json_str)
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ResultMessage':
        """从字典创建"""
        return cls(**data)


def parse_message(json_str: str) -> dict:
    """
    解析消息，返回包含 type 字段的字典
    用于快速判断消息类型
    """
    data = json.loads(json_str)
    return data


def is_command_message(data: dict) -> bool:
    """判断是否为命令消息"""
    return data.get("type") == "command"


def is_result_message(data: dict) -> bool:
    """判断是否为响应消息"""
    return data.get("type") == "result"
