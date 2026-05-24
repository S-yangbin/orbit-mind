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
class MNSConfig:
    """MNS 连接配置"""
    endpoint: str = ""
    access_key_id: str = ""
    access_key_secret: str = ""
    queue_name: str = "mate-notify"


@dataclass
class AgentConfig:
    """Agent 运行配置"""
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


@dataclass
class Config:
    """完整配置"""
    mns: MNSConfig = field(default_factory=MNSConfig)
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

        mns_data = data.get("mns", {})
        if mns_data:
            config.mns.endpoint = mns_data.get("endpoint", config.mns.endpoint)
            config.mns.access_key_id = mns_data.get("access_key_id", config.mns.access_key_id)
            config.mns.access_key_secret = mns_data.get("access_key_secret", config.mns.access_key_secret)
            config.mns.queue_name = mns_data.get("queue_name", config.mns.queue_name)

        agent_data = data.get("agent", {})
        if agent_data:
            config.agent.max_timeout = agent_data.get("max_timeout", config.agent.max_timeout)
            config.agent.allowed_commands = agent_data.get("allowed_commands", config.agent.allowed_commands)
            if "blocked_commands" in agent_data:
                config.agent.blocked_commands = agent_data["blocked_commands"]
            config.agent.working_dir = os.path.expanduser(
                agent_data.get("working_dir", config.agent.working_dir)
            )
            config.agent.log_file = agent_data.get("log_file", config.agent.log_file)
            if "audit_log_dir" in agent_data:
                config.agent.audit_log_dir = os.path.expanduser(agent_data["audit_log_dir"])

    # 环境变量覆盖
    config.mns.endpoint = os.environ.get("MNS_ENDPOINT", config.mns.endpoint)
    config.mns.access_key_id = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID", config.mns.access_key_id)
    config.mns.access_key_secret = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET", config.mns.access_key_secret)
    config.mns.queue_name = os.environ.get("MNS_QUEUE_NAME", config.mns.queue_name)

    return config


def validate_config(config: Config) -> List[str]:
    """验证配置完整性，返回错误信息列表"""
    errors = []
    if not config.mns.endpoint:
        errors.append("MNS endpoint 未配置 (MNS_ENDPOINT)")
    if not config.mns.access_key_id:
        errors.append("AccessKey ID 未配置 (ALIBABA_CLOUD_ACCESS_KEY_ID)")
    if not config.mns.access_key_secret:
        errors.append("AccessKey Secret 未配置 (ALIBABA_CLOUD_ACCESS_KEY_SECRET)")
    if not config.mns.queue_name:
        errors.append("MNS 队列名称未配置 (MNS_QUEUE_NAME)")
    if config.agent.working_dir and not Path(config.agent.working_dir).exists():
        errors.append(f"工作目录不存在: {config.agent.working_dir}")
    return errors
