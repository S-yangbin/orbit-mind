"""
EPD-nRF5 CLI 命令定义

基于 Typer 框架的命令行界面，包含所有子命令实现。
"""

import asyncio
import json
import platform
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint

from .constants import Cmd, EPD_MODELS
from .config import _load_config, _save_address, _get_saved_address
from .image_processing import _generate_dry_run_preview
from .adapter import _resolve_adapter, _list_adapters, scan_devices
from .ble_client import EPDClient, send_image_to_device
from .daily_quote import (
    generate_daily_quote_image,
    _pick_quote,
    _fetch_weather,
    get_weekday_zh,
    get_weekday_en,
)


# ============================================================
# 输出工具
# ============================================================

def output_result(data: dict, json_output: bool = False):
    """统一输出结果，支持 JSON 格式"""
    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for k, v in data.items():
            typer.echo(f"{k}: {v}")


def output_ok(msg: str, json_output: bool = False):
    """输出成功信息"""
    if json_output:
        typer.echo(json.dumps({"ok": msg}, ensure_ascii=False))
    else:
        typer.echo(msg)


# ============================================================
# Typer 应用 & 公共选项
# ============================================================

app = typer.Typer(
    name="epd-tool",
    help="EPD-nRF5 电子墨水屏 BLE 命令行工具",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


def _resolve_address(address: Optional[str]) -> str:
    """解析设备地址: 优先使用命令行参数，否则从配置/环境变量读取"""
    if address:
        return address
    saved = _get_saved_address()
    if saved:
        return saved
    typer.echo(
        "错误: 未指定设备地址。请通过以下方式之一提供:\n"
        "  1. 命令行 -a/--address 参数\n"
        "  2. 环境变量 EPD_ADDRESS\n"
        "  3. 先执行 epd-tool scan 扫描设备或 epd-tool connect 连接设备",
        err=True,
    )
    raise typer.Exit(code=1)


def _warn_macos_adapter(adapter: Optional[str]) -> None:
    """在 macOS 上提示用户 adapter 参数无效"""
    if adapter:
        if platform.system() == "Darwin":
            typer.echo(
                f"警告: macOS CoreBluetooth 不支持指定蓝牙适配器，--adapter {adapter} 将被忽略。",
                err=True,
            )


def _make_client(
    address: Optional[str],
    mtu: int = 247,
    interleaved: int = 50,
    adapter: Optional[str] = None,
) -> EPDClient:
    """创建 EPDClient 实例"""
    resolved = _resolve_address(address)
    # 如果未指定 adapter，尝试从保存的配置中读取
    if adapter is None:
        saved_adapter = _load_config().get("last_adapter")
        if saved_adapter:
            adapter = saved_adapter
    _warn_macos_adapter(adapter)
    return EPDClient(resolved, mtu=mtu, interleaved=interleaved, adapter=adapter)


def _parse_hex_int(value: str) -> int:
    """解析十六进制或十进制整数"""
    return int(value, 0)


# ============================================================
# 子命令
# ============================================================

@app.command()
def scan(
    duration: float = typer.Option(5.0, "-d", "--duration", help="扫描时长(秒)"),
    show_all: bool = typer.Option(False, "--all", help="显示所有设备(包括非EPD)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """扫描附近的 EPD 设备"""
    async def _run():
        _warn_macos_adapter(adapter)
        devices = await scan_devices(duration, adapter=adapter)
        epd_devices = [d for d in devices if d["is_epd"]]
        other_devices = [d for d in devices if not d["is_epd"]]

        if json_output:
            typer.echo(json.dumps(devices, ensure_ascii=False, indent=2))
            return

        if epd_devices:
            typer.echo("=== EPD 设备 ===")
            for d in epd_devices:
                rssi = f" RSSI:{d['rssi']}" if d["rssi"] else ""
                typer.echo(f"  {d['address']}  {d['name']}{rssi}")
            # 只有一个 EPD 设备时自动记住地址和名称
            if len(epd_devices) == 1:
                _save_address(epd_devices[0]["address"], epd_devices[0]["name"])
        if other_devices and show_all:
            typer.echo("=== 其他设备 ===")
            for d in other_devices:
                rssi = f" RSSI:{d['rssi']}" if d["rssi"] else ""
                typer.echo(f"  {d['address']}  {d['name']}{rssi}")
        if not devices:
            typer.echo("未发现任何设备")
        elif not epd_devices:
            typer.echo(f"发现 {len(devices)} 个设备，但未找到 EPD 设备 (使用 --all 查看全部)")

    asyncio.run(_run())


@app.command()
def connect(
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """连接设备并读取基本信息"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            info = await client.connect()
            output_result(info, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command()
def info(
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """读取设备固件版本"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            ver = await client.read_version()
            output_result(ver, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command()
def init(
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    driver: Optional[str] = typer.Option(None, "--driver", help="驱动型号 ID (如 0x06)"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """初始化 EPD 驱动"""
    async def _run():
        driver_id = _parse_hex_int(driver) if driver else None
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            result = await client.epd_init(driver_id)
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command()
def clear(
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """清除屏幕（刷为白色）"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            # 必须发送 INIT 以初始化固件端的 EPD 驱动模型 (p_epd->epd)
            # 固件 CLEAR 处理器有 if(p_epd->epd) 守卫，未初始化会静默跳过
            # 使用设备配置中存储的 model_id（不指定则使用固件默认值）
            await client.epd_init(client.driver_id)
            # 发送 CLEAR [0x02]，固件内部会执行 init + fill RAM + refresh
            await client.write_cmd(Cmd.CLEAR)
            # 等待墨水屏全刷完成（SSD16xx 约 4-8 秒，UC81xx 约 3-5 秒）
            # 断开连接时固件 on_disconnect 会调用 sleep()，
            # 必须等刷新完成后再断开，否则 sleep 会中断正在进行的刷新
            typer.echo("正在清屏，请稍候...")
            await asyncio.sleep(8)
            result = {"clear": "ok"}
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command("time")
def sync_time(
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    mode: str = typer.Option("calendar", "--mode", help="显示模式: calendar/clock"),
    timezone: Optional[int] = typer.Option(None, "--timezone", help="时区偏移(小时), 默认自动检测"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """同步时间并设置显示模式"""
    async def _run():
        mode_val = 1 if mode == "calendar" else 2
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            result = await client.set_time(mode=mode_val, timezone=timezone)
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command("week-start")
def week_start(
    day: int = typer.Argument(..., help="0=周日, 1=周一, ..., 6=周六"),
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """设置每周起始日"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            result = await client.set_week_start(day)
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command("set-pins")
def set_pins(
    mosi: int = typer.Option(..., "--mosi", help="MOSI 引脚"),
    sclk: int = typer.Option(..., "--sclk", help="SCLK 引脚"),
    cs: int = typer.Option(..., "--cs", help="CS 引脚"),
    dc: int = typer.Option(..., "--dc", help="DC 引脚"),
    rst: int = typer.Option(..., "--rst", help="RST 引脚"),
    busy: int = typer.Option(..., "--busy", help="BUSY 引脚"),
    bs: int = typer.Option(..., "--bs", help="BS 引脚"),
    en: int = typer.Option(0xFF, "--en", help="EN 引脚 (默认: 0xFF=不使用)"),
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """设置 EPD 引脚映射"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            result = await client.set_pins(mosi, sclk, cs, dc, rst, busy, bs, en)
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command("set-config")
def set_config(
    config: str = typer.Argument(..., help="配置数据(十六进制字符串)"),
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """设置完整 EPD 配置"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            result = await client.set_config(config)
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command("send-cmd")
def send_cmd(
    hex_data: str = typer.Argument(..., help="十六进制数据 (如 '0106')"),
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """发送原始 BLE 命令(十六进制)"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            result = await client.send_raw_cmd(hex_data)
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command("send-image")
def send_image(
    image: Path = typer.Argument(..., help="图片文件路径", exists=True),
    driver: Optional[str] = typer.Option(None, "--driver", help="驱动型号 ID (如 0x06，不指定则自动从设备读取)"),
    dither: str = typer.Option("floyd_steinberg", "--dither", help="抖动算法"),
    strength: float = typer.Option(1.0, "--strength", help="抖动强度 (0-5)"),
    contrast: float = typer.Option(1.2, "--contrast", help="对比度 (0.5-2)"),
    brightness: float = typer.Option(1.0, "--brightness", help="亮度 (0.5-1.5，默认 1.0)"),
    fit: str = typer.Option("stretch", "--fit", help="适配模式: stretch(拉伸)/contain(留白)/cover(裁剪)"),
    slot: Optional[int] = typer.Option(None, "--slot", help="图片槽位编号，指定时图片将保存到该槽位"),
    interleaved: int = typer.Option(10, "--interleaved", help="Write Without Response 间隔数（浏览器默认 10）"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅处理图片并保存预览，不发送到设备"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="预览图输出路径 (默认: 原文件名_preview.png)"),
    no_sleep: bool = typer.Option(False, "--no-sleep", help="发送图片后不将设备进入深度休眠（默认会休眠以保持画面）"),
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """处理图片并发送到设备（颜色模式由驱动型号自动决定，driver不指定时自动从设备读取）
    
    发送完成后默认将设备进入深度休眠以保持画面，使用 --no-sleep 可跳过休眠。
    支持通过 --slot 指定槽位编号，将图片保存到设备槽位中。
    """
    async def _run():
        # dry-run 模式：需要 driver 来确定屏幕参数
        if dry_run:
            if driver is None:
                typer.echo(
                    "错误: --dry-run 模式需要通过 --driver 参数指定驱动型号。\n"
                    "使用 'epd-tool list-drivers' 查看所有支持的型号。",
                    err=True,
                )
                raise typer.Exit(code=1)
            driver_id = _parse_hex_int(driver)
            if driver_id not in EPD_MODELS:
                raise ValueError(f"未知的驱动型号: 0x{driver_id:02x}")
            model_name, mode, w, h, ic = EPD_MODELS[driver_id]
            result = _generate_dry_run_preview(
                str(image), w, h, mode, dither, strength, contrast, brightness, fit, output,
            )
            result["driver"] = f"0x{driver_id:02x}"
            result["model"] = model_name
            output_result(result, json_output)
            return

        client = _make_client(address, mtu, interleaved, adapter=adapter)
        try:
            await client.connect()
            
            # 确定 driver_id，然后调用 epd_init 发送 INIT 并获取正确的 MTU
            if driver is None:
                # 自动识别：INIT 无参数，从 config 通知中读取 driver_id
                if not json_output:
                    typer.echo("正在自动识别设备驱动型号...")
                await client.epd_init()
                if client.driver_id is None:
                    typer.echo(
                        "错误: 无法从设备读取驱动型号。\n"
                        "请通过 --driver 参数手动指定，或使用 'epd-tool init' 命令先初始化设备。",
                        err=True,
                    )
                    raise typer.Exit(code=1)
                driver_id = client.driver_id
                if not json_output:
                    typer.echo(f"自动识别到驱动型号: 0x{driver_id:02x}")
            else:
                # 手动指定：用 driver_id 发送 INIT，同时获取正确的 MTU
                driver_id = _parse_hex_int(driver)
                if not json_output:
                    typer.echo(f"初始化驱动 0x{driver_id:02x}...")
                await client.epd_init(driver_id)

            # 等待 INIT 完成（与浏览器 200ms 延迟一致）
            await asyncio.sleep(0.2)

            # 槽位检查
            if slot is not None:
                # 升级版固件要求 SID ECC 验证
                if client.sid:
                    if not json_output:
                        typer.echo(f"检测到升级版固件，正在验证 SID...")
                    if not await client.validate_sid():
                        typer.echo("错误: SID ECC 验证失败，无法操作槽位。", err=True)
                        typer.echo("请确保设备固件为升级版，或尝试使用 https://epdiy.cn 网页操作。", err=True)
                        raise typer.Exit(code=1)
                elif not json_output:
                    typer.echo("警告: 未收到设备 SID，槽位命令可能无效。", err=True)
                if client.slots is not None:
                    slot_count = client.slots["count"]
                    if slot < 0 or slot >= slot_count:
                        typer.echo(
                            f"错误: 槽位编号 {slot} 超出范围，设备支持 0-{slot_count-1} 个槽位。",
                            err=True,
                        )
                        raise typer.Exit(code=1)
                    used_mask = client.slots["used_mask"]
                    if (used_mask & (1 << slot)) != 0:
                        if not json_output:
                            typer.echo(f"警告: 槽位 {slot} 非空，发送新图片将覆盖原有图片。")
                if not json_output:
                    typer.echo(f"图片将保存到槽位 {slot}")

            result = await client.send_image(
                image_path=str(image),
                driver_id=driver_id,
                dither=dither,
                strength=strength,
                contrast=contrast,
                brightness=brightness,
                fit=fit,
                slot=slot,
            )
            output_result(result, json_output)

            # 默认发送完成后将设备进入深度休眠，防止 WDT 复位导致画面被日历覆盖
            if slot is None and not no_sleep:
                # 普通模式: 使用 SYS_SLEEP 深度休眠
                try:
                    await client.sys_sleep()
                    if not json_output:
                        typer.echo("设备已进入深度休眠，画面将保持显示。")
                except Exception:
                    pass
        finally:
            # 如果已经 sent sys_sleep，设备已断开，disconnect 可能会失败
            try:
                await client.disconnect()
            except Exception:
                pass

    asyncio.run(_run())


@app.command("show-slot")
def show_slot(
    slot_id: int = typer.Argument(..., help="要显示的槽位编号"),
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """显示指定槽位的图片"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            # 与网页版一致：发送 INIT 不带参数，使用设备保存的 model_id
            await client.epd_init()
            
            # 升级版固件要求 SID ECC 验证
            if client.sid:
                if not json_output:
                    typer.echo(f"检测到升级版固件，正在验证 SID...")
                if not await client.validate_sid():
                    typer.echo("错误: SID ECC 验证失败，无法操作槽位。", err=True)
                    typer.echo("请确保设备固件为升级版，或尝试使用 https://epdiy.cn 网页操作。", err=True)
                    raise typer.Exit(code=1)
                if not json_output:
                    typer.echo("SID 验证通过")
            else:
                if not json_output:
                    typer.echo("警告: 未收到设备 SID，槽位命令可能无效。", err=True)
            
            # 步骤1: 设置槽位编号
            if not json_output:
                typer.echo(f"正在设置槽位 {slot_id}...")
            
            # 在发送SET_SLOT前，等待INIT的所有通知都处理完成
            await asyncio.sleep(0.5)
            
            try:
                result = await client.set_slot(mode=1, slot_id=slot_id)
                if not json_output:
                    typer.echo("SET_SLOT命令发送成功")
            except Exception as e:
                # Linux上可能出现GATT协议错误，重试一次
                if not json_output:
                    typer.echo(f"SET_SLOT命令失败，正在重试... ({e})", err=True)
                await asyncio.sleep(2.0)
                result = await client.set_slot(mode=1, slot_id=slot_id)
                if not json_output:
                    typer.echo("SET_SLOT命令重试成功")
            
            # 等待设备处理SET_SLOT命令
            await asyncio.sleep(1.5)
            
            # 步骤2: 发送 SET_TIME(mode=0/PICTURE) 强制触发 GUI 更新
            if not json_output:
                typer.echo(f"正在显示槽位 {slot_id}，请等待屏幕刷新...")
            
            try:
                await client.set_time(mode=0)
            except Exception as e:
                if not json_output:
                    typer.echo(f"SET_TIME命令失败，正在重试... ({e})", err=True)
                await asyncio.sleep(1.0)
                await client.set_time(mode=0)
            
            # 等待固件内部 GUI 更新完成（加载图片 + 刷新屏幕）
            if not json_output:
                typer.echo("等待墨水屏刷新完成...")
            
            await asyncio.sleep(20)
            
            result["refresh_wait"] = "20s"
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command("slots")
def list_slots(
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """查看设备图片槽位状态"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            info = await client.connect()
            # 如果 connect 阶段未收到 slots 通知，发送 INIT 触发（与网页行为一致）
            if client.slots is None:
                await client.epd_init()
                await asyncio.sleep(0.2)
            if client.slots is None:
                if json_output:
                    typer.echo(json.dumps({"slots": None, "message": "设备不支持槽位功能"}, ensure_ascii=False, indent=2))
                else:
                    typer.echo("设备不支持槽位功能（固件版本过低）")
                return
            slots = client.slots
            count = slots["count"]
            used_mask = slots["used_mask"]
            slot_list = []
            for i in range(count):
                used = (used_mask & (1 << i)) != 0
                slot_list.append({"slot": i, "used": used})
            if json_output:
                typer.echo(json.dumps({"count": count, "used_mask": used_mask, "slots": slot_list}, ensure_ascii=False, indent=2))
            else:
                typer.echo(f"槽位总数: {count}，已使用掩码: 0x{used_mask:02x}")
                for s in slot_list:
                    status = "✓ 已用" if s["used"] else "✗ 空"
                    typer.echo(f"  槽位 {s['slot']}: {status}")
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command("free-slot")
def free_slot(
    slot_id: int = typer.Argument(..., help="要删除的槽位编号"),
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """删除指定槽位的图片"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            await client.epd_init()
            # 升级版固件要求 SID ECC 验证
            if client.sid:
                if not json_output:
                    typer.echo(f"检测到升级版固件，正在验证 SID...")
                if not await client.validate_sid():
                    typer.echo("错误: SID ECC 验证失败，无法操作槽位。", err=True)
                    typer.echo("请确保设备固件为升级版，或尝试使用 https://epdiy.cn 网页操作。", err=True)
                    raise typer.Exit(code=1)
            result = await client.free_slot(slot_id)
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command("slide")
def slide(
    interval: int = typer.Argument(..., help="轮播间隔（分钟）"),
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """启动图片轮播模式，按指定间隔循环显示已保存的槽位图片"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            await client.epd_init()
            # 升级版固件要求 SID ECC 验证
            if client.sid:
                if not json_output:
                    typer.echo(f"检测到升级版固件，正在验证 SID...")
                if not await client.validate_sid():
                    typer.echo("错误: SID ECC 验证失败，无法操作槽位。", err=True)
                    typer.echo("请确保设备固件为升级版，或尝试使用 https://epdiy.cn 网页操作。", err=True)
                    raise typer.Exit(code=1)
            result = await client.set_slide(interval)
            output_result(result, json_output)
        finally:
            await client.disconnect()

    asyncio.run(_run())


@app.command()
def reset(
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """系统复位"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            result = await client.sys_reset()
            output_result(result, json_output)
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    asyncio.run(_run())


@app.command()
def sleep(
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """系统进入深度睡眠"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            result = await client.sys_sleep()
            output_result(result, json_output)
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    asyncio.run(_run())


@app.command()
def erase(
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (MAC)"),
    adapter: Optional[str] = typer.Option(None, "--adapter", help="蓝牙适配器(接口名如 hci0/hci1，或 MAC 地址，仅 Linux)"),
    mtu: int = typer.Option(247, "--mtu", help="BLE MTU 大小"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """擦除配置并复位"""
    async def _run():
        client = _make_client(address, mtu, adapter=adapter)
        try:
            await client.connect()
            result = await client.cfg_erase()
            output_result(result, json_output)
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    asyncio.run(_run())


@app.command("list-adapters")
def list_adapters(
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """列出系统上可用的蓝牙适配器（仅 Linux）"""
    if platform.system() == "Darwin":
        if json_output:
            typer.echo(json.dumps({"adapters": [], "message": "macOS 不支持列出适配器"}, ensure_ascii=False, indent=2))
        else:
            typer.echo("macOS CoreBluetooth 不支持列出适配器")
        return

    adapters = _list_adapters()
    if json_output:
        typer.echo(json.dumps({"adapters": adapters}, ensure_ascii=False, indent=2))
    elif adapters:
        typer.echo(f"{'接口':<10} {'MAC 地址':<20} {'默认'}")
        typer.echo("-" * 45)
        for a in adapters:
            default = "✓" if a["default"] else ""
            typer.echo(f"{a['name']:<10} {a['mac']:<20} {default}")
    else:
        typer.echo("未找到蓝牙适配器")


@app.command("list-drivers")
def list_drivers(
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """列出所有支持的 EPD 驱动型号"""
    if json_output:
        result = []
        for did, (name, mode, w, h, ic) in EPD_MODELS.items():
            result.append({
                "id": f"0x{did:02x}",
                "name": name,
                "mode": mode,
                "width": w,
                "height": h,
                "ic": ic,
            })
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        typer.echo(f"{'ID':<6} {'型号':<30} {'模式':<8} {'分辨率':<12} {'IC'}")
        typer.echo("-" * 75)
        for did, (name, mode, w, h, ic) in sorted(EPD_MODELS.items()):
            typer.echo(f"0x{did:02x}   {name:<30} {mode:<8} {w}x{h:<8} {ic}")


@app.command("daily-quote")
def daily_quote(
    weather: Optional[str] = typer.Option(None, "--weather", "-w", help="天气描述 (如 '晴 25°C')，不提供则自动获取"),
    quote: Optional[str] = typer.Option(None, "--quote", "-q", help="箴言内容，不提供则随机选择"),
    city: str = typer.Option("杭州", "--city", "-c", help="城市名 (用于自动获取天气)"),
    width: int = typer.Option(400, "--width", help="图片宽度 (像素)"),
    height: int = typer.Option(300, "--height", help="图片高度 (像素)"),
    output: str = typer.Option("daily_quote.png", "--output", "-o", help="输出文件路径"),
    font: Optional[str] = typer.Option(None, "--font", help="字体文件路径 (默认自动查找系统中文字体)"),
    send: bool = typer.Option(False, "--send", help="生成后直接发送到设备"),
    address: Optional[str] = typer.Option(None, "-a", "--address", help="BLE 设备地址 (配合 --send 使用)"),
    driver: Optional[str] = typer.Option(None, "--driver", help="驱动型号 (配合 --send 使用)"),
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出"),
):
    """生成每日箴言图片，包含日期、星期、天气和箴言，使用红白黑三色"""
    import datetime

    now = datetime.datetime.now()
    date_str = now.strftime("%Y年%m月%d日")
    weekday = get_weekday_zh(now.weekday())
    weekday_en = get_weekday_en(now.weekday())

    # 天气
    weather_text = weather
    if weather_text is None:
        if not json_output:
            typer.echo(f"正在获取 {city} 的天气信息...")
        weather_data = _fetch_weather(city)
        if weather_data:
            parts = []
            if weather_data["desc"]:
                parts.append(weather_data["desc"])
            if weather_data["temp"]:
                parts.append(f"{weather_data['temp']}°C")
            weather_text = " ".join(parts)
        else:
            if not json_output:
                typer.echo("无法获取天气信息，跳过天气显示")
            weather_text = ""

    # 箴言
    quote_text = quote
    if quote_text is None:
        quote_text = _pick_quote()

    result = generate_daily_quote_image(
        width=width, height=height,
        date_str=date_str, weekday=weekday,
        weather_text=weather_text,
        quote_text=quote_text,
        font_path=font,
        output_path=output,
        weekday_en=weekday_en,
        weather_desc_raw=weather_text if weather_text else "",
    )

    if not json_output:
        typer.echo(f"✓ 每日箴言图片已生成: {output}")
        typer.echo(f"  日期: {date_str} {weekday}")
        if weather_text:
            typer.echo(f"  天气: {weather_text}")
        typer.echo(f"  箴言: {quote_text}")

    # 发送到设备
    if send:
        if not json_output:
            typer.echo("正在发送图片到设备...")

        driver_id = _parse_hex_int(driver) if driver else None

        async def _send():
            send_result = await send_image_to_device(
                address=_resolve_address(address),
                image_path=output,
                driver_id=driver_id,
                sys_sleep_after=True,
            )
            result["send_result"] = send_result

        asyncio.run(_send())
        if not json_output:
            typer.echo("✓ 图片已发送到设备")

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
