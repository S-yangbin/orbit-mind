"""
EPD-nRF5 BLE 客户端

包含 EPDClient 类，负责与 EPD 设备的 BLE 通信、命令发送、图片传输等。
"""

import asyncio
import struct
import time
import urllib.parse
import urllib.request
from typing import Optional

try:
    from bleak import BleakClient, BleakScanner
    from bleak.backends.characteristic import BleakGATTCharacteristic
except ImportError:
    import typer
    typer.echo("错误: 需要安装 bleak 库。请运行: pip install bleak", err=True)
    raise SystemExit(1)

from .constants import (
    Cmd,
    EPD_CHAR_UUID,
    EPD_MODELS,
    EPD_SERVICE_UUID,
    APP_VER_UUID,
)
from .config import _save_address
from .adapter import _resolve_adapter
from .image_processing import (
    convert_uc8159,
    load_and_process_image,
)


# ============================================================
# BLE 通信层
# ============================================================

class EPDClient:
    """EPD-nRF5 BLE 客户端"""

    def __init__(self, address: str, mtu: int = 247, interleaved: int = 50,
                 timeout: float = 30.0, adapter: Optional[str] = None):
        self.address = address
        self.mtu = mtu
        self.interleaved = interleaved
        self.timeout = timeout
        self.adapter = adapter
        self.client: Optional[BleakClient] = None
        self.epd_char: Optional[BleakGATTCharacteristic] = None
        self.ver_char: Optional[BleakGATTCharacteristic] = None
        self.notifications = []
        self.app_version = 0
        self.device_mtu = 20
        self.device_config = None
        self.driver_id: Optional[int] = None
        self.slots: Optional[dict] = None  # {"count": int, "used_mask": int}
        self.sid: Optional[str] = None
        self.sid_validated: bool = False  # ECC SID 验证状态
        self.device_name: Optional[str] = None
        self._notify_event = asyncio.Event()

    async def connect(self):
        """连接设备并发现服务"""
        self.client = await self._create_client()
        # 尝试协商 MTU（bleak 3.x 在 macOS 上由系统自动协商，无 request_mtu）
        try:
            if self.mtu > 23 and hasattr(self.client, 'request_mtu'):
                await self.client.request_mtu(self.mtu)
                self.device_mtu = self.mtu - 3
            else:
                self.device_mtu = self.mtu - 3  # 使用用户配置值
        except Exception:
            self.device_mtu = self.mtu - 3
        for service in self.client.services:
            if service.uuid == EPD_SERVICE_UUID:
                for char in service.characteristics:
                    if char.uuid == EPD_CHAR_UUID:
                        self.epd_char = char
                    elif char.uuid == APP_VER_UUID:
                        self.ver_char = char
        if not self.epd_char:
            raise RuntimeError("未找到 EPD Characteristic")
        if self.ver_char:
            ver_data = await self.client.read_gatt_char(self.ver_char)
            self.app_version = ver_data[0]
        await self.client.start_notify(self.epd_char, self._on_notify)
        # 等待设备发送 config 通知（在订阅后立即发送）
        # 升级版固件会依次发送: 二进制config、slots=、sid=、clock_enable= 等
        # 需要足够长的等待时间来确保所有通知都到达
        try:
            await asyncio.wait_for(self._notify_event.wait(), timeout=2.0)
            self._notify_event.clear()
            # 收到第一个通知后，等待其余文本通知（slots=, sid= 等）到达
            # 升级版固件的文本通知可能有延迟，需等待更长时间
            for _ in range(10):  # 最多等 2 秒 (10 x 0.2s)
                await asyncio.sleep(0.2)
                if self._notify_event.is_set():
                    self._notify_event.clear()
        except asyncio.TimeoutError:
            pass
        # 解析 connect 阶段的 config 通知（提取 driver_id、slots 等）
        for notif in self.notifications:
            self._parse_config(notif)
        self.notifications.clear()
        result = {
            "connected": True,
            "address": self.address,
            "name": self.device_name,
            "app_version": f"0x{self.app_version:02x}",
            "mtu": self.device_mtu,
            "driver_id": f"0x{self.driver_id:02x}" if self.driver_id is not None else None,
        }
        if self.slots is not None:
            result["slots"] = self.slots
        if self.sid is not None:
            result["sid"] = self.sid
        # 连接成功后自动保存设备地址和名称（供后续连接时按名称匹配）
        _save_address(self.address, self.device_name or "", adapter=self.adapter)
        return result

    async def disconnect(self):
        """断开连接"""
        if self.client and self.client.is_connected:
            try:
                await self.client.stop_notify(self.epd_char)
            except Exception:
                pass
            await self.client.disconnect()

    async def _create_client(self) -> BleakClient:
        """创建 BleakClient 并连接

        macOS 上 CoreBluetooth UUID 跨进程变化，直连必定失败，必须扫描后用 BLEDevice 连接。
        使用 find_device_by_filter，找到 NRF_EPD 设备即返回，无需等满扫描超时。
        """
        # macOS CoreBluetooth 不支持指定适配器，忽略 adapter 参数
        import platform
        _is_macos = platform.system() == "Darwin"
        adapter_kwargs = {}
        if self.adapter and not _is_macos:
            adapter_kwargs["adapter"] = _resolve_adapter(self.adapter)

        # 快速扫描: find_device_by_filter 找到 NRF_EPD 即返回（通常 1-3s）
        try:
            device = await BleakScanner.find_device_by_filter(
                lambda d, adv: (d.name or adv.local_name or "").startswith("NRF_EPD"),
                timeout=15.0,
                **adapter_kwargs,
            )
            if device:
                self.address = device.address
                self.device_name = device.name or ""
                client = BleakClient(device, timeout=self.timeout, **adapter_kwargs)
                await client.connect()
                return client
        except Exception:
            pass

        # 兜底: 非 macOS 平台尝试 MAC 地址直连
        if not _is_macos:
            try:
                client = BleakClient(self.address, timeout=self.timeout, **adapter_kwargs)
                await client.connect()
                return client
            except Exception:
                pass

        raise RuntimeError(
            "扫描未找到 EPD 设备 (NRF_EPD_*)。请确认:\n"
            "  1. 设备已开机且在蓝牙范围内\n"
            "  2. 设备未连接其他设备（如网页版）\n"
            "  3. 执行 epd-tool scan --all 查看全部设备"
        )

    def _on_notify(self, char: BleakGATTCharacteristic, data: bytearray):
        self.notifications.append(bytes(data))
        self._notify_event.set()

    async def _write(self, data: bytes, with_response: bool = True):
        if not self.client or not self.client.is_connected:
            raise RuntimeError("设备未连接")
        if with_response:
            await self.client.write_gatt_char(self.epd_char, data, response=True)
        else:
            await self.client.write_gatt_char(self.epd_char, data, response=False)

    async def write_cmd(self, cmd: Cmd, payload: bytes = b""):
        data = bytes([cmd]) + payload
        await self._write(data, with_response=True)

    async def read_version(self) -> dict:
        if self.ver_char:
            ver_data = await self.client.read_gatt_char(self.ver_char)
            self.app_version = ver_data[0]
        return {"app_version": f"0x{self.app_version:02x}"}

    def _parse_config(self, notif: bytes) -> dict:
        """解析设备通知，提取 driver_id、MTU、槽位等信息"""
        result = {}
        # 判断是否为文本通知：所有字节都是可打印 ASCII (0x20-0x7E)
        is_text = all(0x20 <= b <= 0x7E for b in notif)
        if is_text:
            text = notif.decode("ascii")
            if text.startswith("mtu="):
                self.device_mtu = int(text[4:])
                result["device_mtu"] = self.device_mtu
            elif text.startswith("t="):
                result["device_time"] = int(text[2:])
            elif text.startswith("slots=") and len(text) > 6:
                # 格式: slots=<count> [usedMask] [selectedSlot]
                parts = text[6:].split()
                count = int(parts[0])
                used_mask = int(parts[1]) if len(parts) > 1 else 0
                self.slots = {"count": count, "used_mask": used_mask}
                result["slots"] = self.slots
                if len(parts) > 2:
                    result["selected_slot"] = int(parts[2])
            elif text.startswith("sid=") and len(text) > 4:
                self.sid = text[4:]
                result["sid"] = self.sid
            # 其他文本通知忽略
            return result
        # 解析为二进制配置数据（pins + driver，包含非打印字符）
        if len(notif) >= 8:
            self.device_config = notif
            self.driver_id = notif[7]
            result["config_hex"] = notif.hex()
            result["driver_id"] = f"0x{self.driver_id:02x}"
        return result

    async def epd_init(self, driver_id: Optional[int] = None) -> dict:
        payload = bytes([driver_id]) if driver_id is not None else b""
        # 先解析 connect() 阶段可能残留的通知（如 slots=, sid= 等），再清空
        for notif in self.notifications:
            self._parse_config(notif)
        self.notifications.clear()
        await self.write_cmd(Cmd.INIT, payload)
        result = {"init": "ok"}
        # INIT 命令会发送 mtu= 和 t= 两个文本通知，必须等到 mtu= 到达
        got_mtu_update = False
        deadline = asyncio.get_event_loop().time() + 3.0
        while asyncio.get_event_loop().time() < deadline:
            remaining_time = deadline - asyncio.get_event_loop().time()
            if remaining_time <= 0:
                break
            try:
                await asyncio.wait_for(self._notify_event.wait(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            self._notify_event.clear()
            # 解析所有未处理的通知
            for notif in self.notifications:
                parsed = self._parse_config(notif)
                result.update(parsed)
                if "device_mtu" in parsed:
                    got_mtu_update = True
            # 收到 MTU 更新后可以退出
            if got_mtu_update:
                break
        # MTU 到达后，继续等待可能延迟到达的文本通知（sid=, slots=, clock_enable= 等）
        # 升级版固件的 sid= 可能在 MTU 之后异步发送
        if self.sid is None:
            sid_deadline = asyncio.get_event_loop().time() + 3.0
            while asyncio.get_event_loop().time() < sid_deadline:
                try:
                    await asyncio.wait_for(self._notify_event.wait(), timeout=0.5)
                except asyncio.TimeoutError:
                    break  # 0.5秒无新通知，认为通知已全部到达
                self._notify_event.clear()
                for notif in self.notifications:
                    parsed = self._parse_config(notif)
                    result.update(parsed)
                if self.sid is not None:
                    break
        # 最后一次扫描所有通知
        for notif in self.notifications:
            parsed = self._parse_config(notif)
            result.update(parsed)
        self.notifications.clear()
        return result

    async def clear_screen(self) -> dict:
        await self.write_cmd(Cmd.CLEAR)
        return {"clear": "ok"}

    async def validate_sid(self) -> bool:
        """验证升级版固件的 ECC SID 认证
        
        升级版固件要求 SID 验证通过后才能使用槽位相关命令（SET_SLOT/FREE_SLOT/SET_SLIDE）。
        参考升级版网页实现：POST sid hash 到 https://epdiy.cn/ecc/check
        """
        if not self.sid:
            # 未收到 sid=，可能固件未发送或通知丢失，尝试额外等待
            if not await self.wait_for_sid(timeout=3.0):
                return True  # 确实没有 SID，视为老固件
        if self.sid_validated:
            return True
        def _check():
            data = urllib.parse.urlencode({"hash": self.sid}).encode("utf-8")
            req = urllib.request.Request("https://epdiy.cn/ecc/check", data=data, method="POST")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.read().decode("utf-8").strip()
        try:
            result = await asyncio.to_thread(_check)
            self.sid_validated = (result == "OK")
        except Exception as e:
            self.sid_validated = False
        return self.sid_validated

    async def wait_for_sid(self, timeout: float = 3.0) -> bool:
        """等待 sid= 通知到达
        
        升级版固件的 sid= 可能在 INIT 之后异步发送，
        此方法提供一个专用的等待窗口。
        """
        if self.sid is not None:
            return True
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                await asyncio.wait_for(self._notify_event.wait(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            self._notify_event.clear()
            for notif in self.notifications:
                self._parse_config(notif)
            if self.sid is not None:
                self.notifications.clear()
                return True
        self.notifications.clear()
        return self.sid is not None

    async def set_time(self, mode: int = 1, timezone: Optional[int] = None) -> dict:
        ts = int(time.time())
        if timezone is None:
            import time as _time
            timezone = -int(_time.timezone // 3600) if _time.daylight == 0 else -int(_time.altzone // 3600)
        payload = struct.pack(">IbB", ts, timezone, mode)
        await self.write_cmd(Cmd.SET_TIME, payload)
        return {"set_time": "ok", "timestamp": ts, "timezone": timezone, "mode": mode}

    async def set_week_start(self, day: int) -> dict:
        if day < 0 or day > 6:
            raise ValueError("day 必须在 0-6 之间")
        await self.write_cmd(Cmd.SET_WEEK_START, bytes([day]))
        return {"set_week_start": "ok", "day": day}

    async def set_pins(self, mosi: int, sclk: int, cs: int, dc: int,
                       rst: int, busy: int, bs: int, en: int = 0xFF) -> dict:
        payload = bytes([mosi, sclk, cs, dc, rst, busy, bs, en])
        await self.write_cmd(Cmd.SET_PINS, payload)
        return {"set_pins": "ok"}

    async def set_config(self, config_hex: str) -> dict:
        config_bytes = bytes.fromhex(config_hex)
        await self.write_cmd(Cmd.SET_CONFIG, config_bytes)
        return {"set_config": "ok"}

    async def send_raw_cmd(self, hex_str: str) -> dict:
        data = bytes.fromhex(hex_str)
        await self._write(data, with_response=True)
        return {"send_cmd": "ok", "hex": hex_str}

    async def send_epd_command(self, cmd_byte: int) -> dict:
        await self.write_cmd(Cmd.SEND_COMMAND, bytes([cmd_byte]))
        return {"epd_command": f"0x{cmd_byte:02x}"}

    async def send_epd_data(self, data_hex: str) -> dict:
        data = bytes.fromhex(data_hex)
        await self.write_cmd(Cmd.SEND_DATA, data)
        return {"epd_data": data_hex}

    async def refresh(self) -> dict:
        await self.write_cmd(Cmd.REFRESH)
        return {"refresh": "ok"}

    async def sleep(self) -> dict:
        await self.write_cmd(Cmd.SLEEP)
        return {"sleep": "ok"}

    async def sys_reset(self) -> dict:
        await self.write_cmd(Cmd.SYS_RESET)
        return {"sys_reset": "ok"}

    async def sys_sleep(self) -> dict:
        await self.write_cmd(Cmd.SYS_SLEEP)
        return {"sys_sleep": "ok"}

    async def cfg_erase(self) -> dict:
        await self.write_cmd(Cmd.CFG_ERASE)
        return {"cfg_erase": "ok"}

    async def set_slot(self, mode: int, slot_id: int) -> dict:
        """设置图片槽位

        Args:
            mode: 0=保存图片到指定槽位，1=显示指定槽位图片
            slot_id: 槽位编号
        """
        await self.write_cmd(Cmd.SET_SLOT, bytes([mode, slot_id]))
        return {"set_slot": "ok", "mode": mode, "slot": slot_id}

    async def free_slot(self, slot_id: int) -> dict:
        """删除指定槽位的图片"""
        await self.write_cmd(Cmd.FREE_SLOT, bytes([slot_id]))
        return {"free_slot": "ok", "slot": slot_id}

    async def set_slide(self, interval_minutes: int) -> dict:
        """启动图片轮播模式

        Args:
            interval_minutes: 轮播间隔（分钟）
        """
        payload = bytes([(interval_minutes >> 8) & 0xFF, interval_minutes & 0xFF])
        await self.write_cmd(Cmd.SET_SLIDE, payload)
        return {"set_slide": "ok", "interval_minutes": interval_minutes}

    async def send_image(
        self,
        image_path: str,
        driver_id: int,
        dither: str = "floyd_steinberg",
        strength: float = 1.0,
        contrast: float = 1.2,
        brightness: float = 1.0,
        fit: str = "stretch",
        slot: Optional[int] = None,
    ) -> dict:
        """处理并发送图片（调用前必须先执行 epd_init）

        Args:
            slot: 图片槽位编号，指定时将图片保存到该槽位而非直接显示
        """
        if driver_id not in EPD_MODELS:
            raise ValueError(f"未知的驱动型号: 0x{driver_id:02x}")

        model_name, mode, w, h, ic = EPD_MODELS[driver_id]

        start = time.time()
        processed = load_and_process_image(
            image_path, w, h, mode, dither, strength, contrast, brightness, fit
        )
        process_time = time.time() - start

        chunk_size = self.device_mtu - 2
        is_uc8159 = ic == "UC8159"
        no_reply_count = self.interleaved

        start = time.time()
        total_chunks = 0

        # 槽位模式: SET_SLOT [0, slot] 保存图片到 flash
        if slot is not None:
            await self.write_cmd(Cmd.SET_SLOT, bytes([0, slot]))
            # 升级版网页: SET_SLOT 后再发一次 INIT，重新初始化显示状态
            await self.write_cmd(Cmd.INIT)
            await asyncio.sleep(0.2)

        # 发送图片数据到显示 RAM
        if mode == "3color" and is_uc8159:
            half = len(processed) // 2
            bw_data = processed[:half]
            rw_data = processed[half:]
            pixel_count = w * h
            combined = convert_uc8159(bw_data, rw_data, pixel_count)
            total_chunks = await self._write_image_chunks(combined, chunk_size, no_reply_count, "bw")
        elif mode == "3color":
            half = len(processed) // 2
            bw_data = processed[:half]
            rw_data = processed[half:]
            n1 = await self._write_image_chunks(bw_data, chunk_size, no_reply_count, "bw")
            n2 = await self._write_image_chunks(rw_data, chunk_size, no_reply_count, "red")
            total_chunks = n1 + n2
        elif mode == "bw" and is_uc8159:
            # UC8159 黑白模式：生成空的红白数据，使用 convert_uc8159 转换
            pixel_count = w * h
            bw_len = (pixel_count + 7) // 8
            empty_rw = bytes(bw_len) if len(processed) < bw_len else bytes(len(processed))
            combined = convert_uc8159(processed[:bw_len], empty_rw, pixel_count)
            total_chunks = await self._write_image_chunks(combined, chunk_size, no_reply_count, "bw")
        else:
            total_chunks = await self._write_image_chunks(processed, chunk_size, no_reply_count, "bw")

        # 等待图片数据写入完成
        await asyncio.sleep(1)

        # 发送 REFRESH 触发屏幕刷新（与升级版网页一致）
        await self.write_cmd(Cmd.REFRESH)

        # 等待墨水屏刷新完成
        # SSD1619 三色屏刷新可能需要 20-30 秒，必须等待足够长时间
        # 如果刷新未完成就 disconnect，on_disconnect 会调用 drv->sleep() 中断刷新
        refresh_wait = 30 if mode in ("3color", "4color") else 8
        await asyncio.sleep(refresh_wait)

        send_time = time.time() - start

        result = {
            "send_image": "ok",
            "driver": f"0x{driver_id:02x}",
            "model": model_name,
            "size": f"{w}x{h}",
            "mode": mode,
            "dither": dither,
            "fit": fit,
            "process_time": f"{process_time:.2f}s",
            "send_time": f"{send_time:.2f}s",
            "total_chunks": total_chunks,
            "refresh_wait": f"{refresh_wait:.0f}s",
        }
        if slot is not None:
            result["slot"] = slot
        return result

    async def _write_image_chunks(self, data: bytes, chunk_size: int,
                                   no_reply_count: int, step: str) -> int:
        count = 0
        remaining = no_reply_count
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            cfg = (0x00 if i == 0 else 0xF0) | (0x0F if step == "bw" else 0x00)
            payload = bytes([Cmd.WRITE_IMAGE, cfg]) + chunk
            with_response = remaining <= 0
            await self._write(payload, with_response=with_response)
            if with_response:
                remaining = no_reply_count
            else:
                remaining -= 1
            count += 1
        return count


# ============================================================
# 可复用的图片发送助手
# ============================================================

async def send_image_to_device(
    address: str,
    image_path: str,
    driver_id: Optional[int],
    mtu: int = 247,
    interleaved: int = 50,
    adapter: Optional[str] = None,
    dither: str = "floyd_steinberg",
    strength: float = 1.0,
    contrast: float = 1.2,
    brightness: float = 1.0,
    fit: str = "stretch",
    slot: Optional[int] = None,
    no_sleep: bool = False,
    sys_sleep_after: bool = False,
) -> dict:
    """连接设备、初始化驱动、发送图片，返回结果字典

    供 send-image 和 daily-quote --send 等命令复用。
    """
    client = EPDClient(address, mtu=mtu, interleaved=interleaved, adapter=adapter)
    try:
        await client.connect()

        # 确定 driver_id
        if driver_id is None:
            await client.epd_init()
            if client.driver_id is None:
                raise RuntimeError(
                    "无法从设备读取驱动型号。\n"
                    "请通过 --driver 参数手动指定，或使用 'epd-tool init' 命令先初始化设备。"
                )
            driver_id = client.driver_id
        else:
            await client.epd_init(driver_id)

        await asyncio.sleep(0.2)

        result = await client.send_image(
            image_path=image_path,
            driver_id=driver_id,
            dither=dither,
            strength=strength,
            contrast=contrast,
            brightness=brightness,
            fit=fit,
            slot=slot,
        )

        if sys_sleep_after and slot is None and not no_sleep:
            try:
                await client.sys_sleep()
                result["sys_sleep"] = "ok"
            except Exception:
                pass

        return result
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
