"""
配置管理模块
从 YAML 文件和环境变量读取配置，环境变量优先级更高
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class AgentConfig:
    """Agent 运行配置"""
    node_id: str = ""  # 节点标识，默认自动生成为 hostname
    max_timeout: int = 120
    allowed_commands: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(default_factory=lambda: [
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd if=/dev/zero of=/dev",
        ":(){ :|:& };:",
    ])
    working_dir: str = os.path.expanduser("~")
    log_file: Optional[str] = None
    audit_log_dir: Optional[str] = None  # 审计日志目录，None 则默认 ~/orbit-mind/logs/
    
    # WebSocket 配置
    mars_sandbox_url: str = "ws://localhost:8888"  # mars-sandbox WebSocket 地址
    node_secret: str = ""  # 节点密钥（用于 WebSocket 连接认证）
    heartbeat_interval: int = 60  # 心跳间隔（秒）
    reconnect_delay: int = 5  # 重连延迟（秒）
    max_reconnect_attempts: int = 0  # 最大重连次数，0 表示无限重试


@dataclass
class Config:
    """完整配置"""
    agent: AgentConfig = field(default_factory=AgentConfig)


def load_config(config_path: Optional[str] = None) -> Config:
    """
    加载配置
    优先级：环境变量 > 配置文件 > 默认值
    """
    config = Config()

    # 查找配置文件
    if config_path is None:
        search_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path.home() / "configs" / "home-agent.yaml",
            Path.home() / ".config" / "orbit-mind" / "config.yaml",
        ]
        for path in search_paths:
            if path.exists():
                config_path = str(path)
                break

    # 从文件加载
    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        agent_data = data.get("agent", {})
        if agent_data:
            config.agent.node_id = agent_data.get("node_id", config.agent.node_id)
            config.agent.max_timeout = agent_data.get("max_timeout", config.agent.max_timeout)
            config.agent.allowed_commands = agent_data.get("allowed_commands", config.agent.allowed_commands)
            if "blocked_commands" in agent_data:
                config.agent.blocked_commands = agent_data["blocked_commands"]
            config.agent.working_dir = os.path.expanduser(
                agent_data.get("working_dir", config.agent.working_dir)
            )
            config.agent.log_file = agent_data.get("log_file", config.agent.log_file)
            if agent_data.get("audit_log_dir"):
                config.agent.audit_log_dir = os.path.expanduser(agent_data["audit_log_dir"])
            
            # WebSocket 配置
            if "mars_sandbox_url" in agent_data:
                config.agent.mars_sandbox_url = agent_data["mars_sandbox_url"]
            if "node_secret" in agent_data:
                config.agent.node_secret = agent_data["node_secret"]
            config.agent.heartbeat_interval = agent_data.get("heartbeat_interval", config.agent.heartbeat_interval)
            config.agent.reconnect_delay = agent_data.get("reconnect_delay", config.agent.reconnect_delay)
            config.agent.max_reconnect_attempts = agent_data.get("max_reconnect_attempts", config.agent.max_reconnect_attempts)

    # 环境变量覆盖 (WebSocket 架构)
    config.agent.node_id = os.environ.get("HOME_AGENT_NODE_ID", config.agent.node_id)
    config.agent.mars_sandbox_url = os.environ.get("MARS_SANDBOX_URL", config.agent.mars_sandbox_url)
    config.agent.node_secret = os.environ.get("HOME_AGENT_NODE_SECRET", config.agent.node_secret)

    # 自动生成 node_id（如果未配置）
    if not config.agent.node_id:
        import socket
        config.agent.node_id = socket.gethostname()

    return config


def validate_config(config: Config) -> List[str]:
    """验证配置完整性，返回错误信息列表"""
    errors = []
    if not config.agent.mars_sandbox_url:
        errors.append("mars-sandbox URL 未配置 (MARS_SANDBOX_URL)")
    if not config.agent.node_secret:
        errors.append("节点密钥未配置 (HOME_AGENT_NODE_SECRET)")
    if config.agent.working_dir and not Path(config.agent.working_dir).exists():
        errors.append(f"工作目录不存在: {config.agent.working_dir}")
    return errors
