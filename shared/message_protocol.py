"""
消息协议定义 - 家庭 AI 中枢系统 (WebSocket 架构)
定义节点注册、心跳、命令和响应消息的标准格式
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
import json
import uuid


@dataclass
class RegisterMessage:
    """节点注册消息 (home-agent → mars-sandbox)"""
    type: str = "register"
    node_id: Optional[str] = None
    hostname: Optional[str] = None
    ip: Optional[str] = None
    platform: Optional[str] = None
    version: str = "1.0.0"
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RegisterMessage':
        return cls(**data)


@dataclass
class RegisterAckMessage:
    """注册确认消息 (mars-sandbox → home-agent)"""
    type: str = "register_ack"
    status: str = "success"
    message: str = "注册成功"
    server_time: Optional[str] = None
    
    def __post_init__(self):
        if self.server_time is None:
            self.server_time = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RegisterAckMessage':
        return cls(**data)


@dataclass
class HeartbeatMessage:
    """心跳消息 (home-agent → mars-sandbox)"""
    type: str = "heartbeat"
    node_id: Optional[str] = None
    uptime_seconds: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HeartbeatMessage':
        return cls(**data)


@dataclass
class HeartbeatAckMessage:
    """心跳确认消息 (mars-sandbox → home-agent)"""
    type: str = "heartbeat_ack"
    status: str = "ok"
    server_time: Optional[str] = None
    
    def __post_init__(self):
        if self.server_time is None:
            self.server_time = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HeartbeatAckMessage':
        return cls(**data)


@dataclass
class CommandMessage:
    """命令消息 (mars-sandbox → home-agent)"""
    command: str
    request_id: Optional[str] = None
    type: str = "command"
    timeout: int = 30  # 命令执行超时时间（秒）
    source: str = "hermes"
    created_at: Optional[str] = None
    
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
    """响应消息 (home-agent → mars-sandbox)"""
    request_id: Optional[str] = None
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    type: str = "result"
    duration_ms: int = 0
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
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


@dataclass
class ErrorMessage:
    """错误消息 (双向)"""
    error_code: str
    message: str
    request_id: Optional[str] = None
    type: str = "error"
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ErrorMessage':
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
