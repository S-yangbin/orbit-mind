"""
EPD-nRF5 配置持久化

管理设备地址记忆、配置文件读写。
"""

import json
import os
from pathlib import Path
from typing import Optional


# ============================================================
# 配置文件路径
# ============================================================

CONFIG_DIR = Path.home() / ".config" / "epd-tool"
CONFIG_FILE = CONFIG_DIR / "config.json"


# ============================================================
# 配置读写
# ============================================================

def _load_config() -> dict:
    """读取保存的配置"""
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_config(data: dict):
    """保存配置到文件"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # 合并已有配置
        existing = _load_config()
        existing.update(data)
        CONFIG_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ============================================================
# 地址管理
# ============================================================

def _save_address(address: str, name: str = "", adapter: Optional[str] = None):
    """保存最近使用的设备地址和名称"""
    data = {"last_address": address}
    if name:
        data["last_device_name"] = name
    if adapter:
        data["last_adapter"] = adapter
    _save_config(data)


def _get_saved_address() -> Optional[str]:
    """获取保存的设备地址"""
    # 优先级: 环境变量 > 配置文件
    return os.environ.get("EPD_ADDRESS") or _load_config().get("last_address")
