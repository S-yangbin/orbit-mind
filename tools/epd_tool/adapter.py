"""
EPD-nRF5 蓝牙适配器管理与设备扫描

包含 Linux 蓝牙适配器发现、MAC 地址解析、BLE 设备扫描等功能。
"""

import platform
from pathlib import Path
from typing import Optional

try:
    from bleak import BleakScanner
except ImportError:
    import typer
    typer.echo("错误: 需要安装 bleak 库。请运行: pip install bleak", err=True)
    raise SystemExit(1)

from .constants import EPD_SERVICE_UUID


# ============================================================
# 蓝牙适配器管理 (Linux)
# ============================================================

def _hci_mac_map() -> dict:
    """从 /sys/class/bluetooth 构建 {hci_name: MAC} 映射"""
    result = {}
    bt_dir = Path("/sys/class/bluetooth")
    if not bt_dir.exists():
        return result
    for hci in sorted(bt_dir.iterdir()):
        addr_file = hci / "address"
        if addr_file.exists():
            try:
                result[hci.name] = addr_file.read_text().strip().upper()
            except PermissionError:
                pass
    return result


def _list_adapters() -> list:
    """列出系统上可用的蓝牙适配器

    优先使用 bluetoothctl list 获取 MAC 和默认标记，
    然后映射到 /sys/class/bluetooth 中的 hci 接口名。
    如果 sysfs 无法提供 hci 名称，则使用 bluetoothctl 的显示名。

    Returns:
        适配器列表，每个元素包含 {"name": "hci0", "mac": "XX:XX:...", "default": bool}
    """
    if platform.system() == "Darwin":
        return []

    # 1. 构建 hci 名称到 MAC 的映射（sysfs + hciconfig）
    hci_map = _hci_mac_map()  # {"hci0": "00:1A:...", "hci1": "60:F6:..."}

    # 补充: 从 hciconfig 获取 hci 名称和 MAC
    if not hci_map:
        try:
            import subprocess
            result = subprocess.run(
                ["hciconfig"], capture_output=True, text=True, timeout=5,
            )
            current_hci = None
            for line in result.stdout.splitlines():
                if not line.startswith((" ", "\t")) and line.strip():
                    current_hci = line.split(":")[0].strip()
                elif "BD Address:" in line and current_hci:
                    mac = line.split("BD Address:")[1].strip().split()[0].upper()
                    hci_map[current_hci] = mac
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    mac_to_hci = {v: k for k, v in hci_map.items()}  # 反向映射

    # 2. 解析 bluetoothctl list 获取 MAC + default 标记
    adapters = []
    seen_macs = set()
    try:
        import subprocess
        result = subprocess.run(
            ["bluetoothctl", "list"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().splitlines():
            # Controller XX:XX:XX:XX:XX:XX display_name [default]
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "Controller":
                mac = parts[1].upper()
                is_default = "[default]" in line
                seen_macs.add(mac)
                # 优先用 sysfs 中的 hci 名称
                hci_name = mac_to_hci.get(mac)
                if hci_name:
                    adapters.append({"name": hci_name, "mac": mac, "default": is_default})
                else:
                    # sysfs 中未找到，使用 MAC 作为标识
                    adapters.append({"name": mac, "mac": mac, "default": is_default})
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 3. 补充 sysfs 中存在但 bluetoothctl 未报告的适配器
    for hci_name, mac in hci_map.items():
        if mac not in seen_macs:
            adapters.append({"name": hci_name, "mac": mac, "default": False})

    return adapters


def _resolve_adapter(adapter: str) -> str:
    """将适配器标识解析为 hci 接口名

    支持以下格式:
      - "hci0", "hci1" 等接口名（直接返回）
      - "00:1A:7D:DA:71:11" 等 MAC 地址（查找对应的 hci 接口名）
    """
    if platform.system() == "Darwin":
        return adapter

    # 已经是 hci 接口名
    if adapter.startswith("hci"):
        return adapter

    # 尝试按 MAC 地址匹配
    mac_upper = adapter.upper()

    # 方法 1: 从 /sys/class/bluetooth 查找
    hci_map = _hci_mac_map()
    for hci_name, mac in hci_map.items():
        if mac == mac_upper:
            return hci_name

    # 方法 2: 从 hciconfig 查找
    try:
        import subprocess
        result = subprocess.run(
            ["hciconfig"], capture_output=True, text=True, timeout=5,
        )
        current_hci = None
        for line in result.stdout.splitlines():
            if not line.startswith((" ", "\t")) and line.strip():
                # hci0:   Type: Primary  Bus: USB
                hci_name = line.split(":")[0].strip()
                current_hci = hci_name
            elif "BD Address:" in line and current_hci:
                #     BD Address: 00:1A:7D:DA:71:11  ACL MTU: 1021:8
                hci_mac = line.split("BD Address:")[1].strip().split()[0].upper()
                if hci_mac == mac_upper:
                    return current_hci
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 未找到匹配，原样返回（让底层报错）
    return adapter


# ============================================================
# 扫描设备 (兼容 bleak 0.21+ 和 3.x)
# ============================================================

async def scan_devices(duration: float = 5.0, adapter: Optional[str] = None) -> list:
    """扫描附近的 EPD 设备

    Args:
        duration: 扫描时长(秒)
        adapter: 蓝牙适配器名称(如 "hci0")、MAC 地址，仅 Linux 有效
    """
    kwargs = {}
    if adapter:
        if platform.system() != "Darwin":
            kwargs["adapter"] = _resolve_adapter(adapter)
    devices = await BleakScanner.discover(timeout=duration, return_adv=True, **kwargs)
    result = []
    for d, adv in devices.values():
        name = d.name or adv.local_name or ""
        uuids = adv.service_uuids or []
        rssi = adv.rssi
        is_epd = name.startswith("NRF_EPD") or EPD_SERVICE_UUID.lower() in [u.lower() for u in uuids]
        result.append({
            "address": d.address,
            "name": name,
            "rssi": rssi,
            "is_epd": is_epd,
        })
    return sorted(result, key=lambda x: (not x["is_epd"], -(x.get("rssi") or -999)))
