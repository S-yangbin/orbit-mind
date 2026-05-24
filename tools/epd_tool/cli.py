#!/usr/bin/env python3
"""
EPD-nRF5 命令行工具 - 通过 BLE 控制电子墨水屏设备

基于 Typer 框架，支持 JSON 输出，方便大模型调用。
"""

import asyncio
import json
import math
import os
import struct
import sys
import time
from enum import IntEnum
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint

import urllib.request
import urllib.parse

try:
    from bleak import BleakClient, BleakScanner
    from bleak.backends.characteristic import BleakGATTCharacteristic
except ImportError:
    typer.echo("错误: 需要安装 bleak 库。请运行: pip install bleak", err=True)
    raise SystemExit(1)

try:
    from PIL import Image
except ImportError:
    typer.echo("错误: 需要安装 Pillow 库。请运行: pip install Pillow", err=True)
    raise SystemExit(1)


# ============================================================
# 常量定义
# ============================================================

EPD_SERVICE_UUID = "62750001-d828-918d-fb46-b6c11c675aec"
EPD_CHAR_UUID = "62750002-d828-918d-fb46-b6c11c675aec"
APP_VER_UUID = "62750003-d828-918d-fb46-b6c11c675aec"
DFU_SERVICE_UUID = "0000fe59-1212-efde-1523-785feabcd123"


class Cmd(IntEnum):
    """EPD 服务命令 ID"""
    SET_PINS = 0x00
    INIT = 0x01
    CLEAR = 0x02
    SEND_COMMAND = 0x03
    SEND_DATA = 0x04
    REFRESH = 0x05
    SLEEP = 0x06
    SET_TIME = 0x20
    SET_WEEK_START = 0x21
    WRITE_IMAGE = 0x30
    SET_SLOT = 0x31
    FREE_SLOT = 0x32
    SET_SLIDE = 0x33
    SET_CONFIG = 0x90
    SYS_RESET = 0x91
    SYS_SLEEP = 0x92
    CFG_ERASE = 0x99


EPD_MODELS = {
    0x01: ("4.2寸黑白(UC8176)", "bw", 400, 300, "UC8176"),
    0x03: ("4.2寸三色(UC8176)", "3color", 400, 300, "UC8176"),
    0x04: ("4.2寸黑白(SSD1619)", "bw", 400, 300, "SSD1619"),
    0x02: ("4.2寸三色(SSD1619)", "3color", 400, 300, "SSD1619"),
    0x05: ("4.2寸四色(JD79668)", "4color", 400, 300, "JD79668"),
    0x0D: ("5.83寸四色(JD79665)", "4color", 648, 480, "JD79665"),
    0x06: ("7.5寸黑白(UC8179)", "bw", 800, 480, "UC8179"),
    0x07: ("7.5寸三色(UC8179)", "3color", 800, 480, "UC8179"),
    0x0C: ("7.5寸四色(JD79665)", "4color", 800, 480, "JD79665"),
    0x08: ("7.5寸低分黑白(UC8159)", "bw", 640, 384, "UC8159"),
    0x09: ("7.5寸低分三色(UC8159)", "3color", 640, 384, "UC8159"),
    0x0A: ("7.5寸HD黑白(SSD1677)", "bw", 880, 528, "SSD1677"),
    0x0B: ("7.5寸HD三色(SSD1677)", "3color", 880, 528, "SSD1677"),
}


# 调色板定义
SIX_COLOR_PALETTE = [
    {"name": "黑色", "r": 0, "g": 0, "b": 0, "value": 0x00},
    {"name": "白色", "r": 255, "g": 255, "b": 255, "value": 0x01},
    {"name": "黄色", "r": 255, "g": 255, "b": 0, "value": 0x02},
    {"name": "红色", "r": 255, "g": 0, "b": 0, "value": 0x03},
    {"name": "蓝色", "r": 0, "g": 0, "b": 255, "value": 0x05},
    {"name": "绿色", "r": 41, "g": 204, "b": 20, "value": 0x06},
]

FOUR_COLOR_PALETTE = [
    {"name": "黑色", "r": 0, "g": 0, "b": 0, "value": 0x00},
    {"name": "白色", "r": 255, "g": 255, "b": 255, "value": 0x01},
    {"name": "红色", "r": 255, "g": 0, "b": 0, "value": 0x03},
    {"name": "黄色", "r": 255, "g": 255, "b": 0, "value": 0x02},
]

THREE_COLOR_PALETTE = [
    {"name": "黑色", "r": 0, "g": 0, "b": 0, "value": 0x00},
    {"name": "白色", "r": 255, "g": 255, "b": 255, "value": 0x01},
    {"name": "红色", "r": 255, "g": 0, "b": 0, "value": 0x02},
]


# ============================================================
# 图像处理 - 颜色空间与调色板
# ============================================================

def rgb_to_lab(r, g, b):
    """RGB 转 CIE Lab 颜色空间"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
    r, g, b = r * 100, g * 100, b * 100
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 95.047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 100.0
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 108.883
    epsilon, kappa = 0.008856, 903.3
    x = x ** (1/3) if x > epsilon else (kappa * x + 16) / 116
    y = y ** (1/3) if y > epsilon else (kappa * y + 16) / 116
    z = z ** (1/3) if z > epsilon else (kappa * z + 16) / 116
    return (116 * y - 16, 500 * (x - y), 200 * (y - z))


def lab_distance(lab1, lab2):
    """计算两个 Lab 颜色之间的感知距离"""
    dl = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(0.2 * dl * dl + 3 * da * da + 3 * db * db)


def find_closest_color(r, g, b, mode):
    """在调色板中找到最接近的颜色（与 epdiy.cn 浏览器版 at() 保持一致）"""
    if mode == "3color":
        # 与 epdiy.cn 浏览器版 at() 保持一致的红色检测
        # 浏览器: e > 120 && e > t*1.5 && e > n*1.5
        if r > 120 and r > g * 1.5 and r > b * 1.5:
            return THREE_COLOR_PALETTE[2]
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        return THREE_COLOR_PALETTE[0] if luminance < 128 else THREE_COLOR_PALETTE[1]

    palette = FOUR_COLOR_PALETTE if mode == "4color" else SIX_COLOR_PALETTE

    if mode not in ("3color", "4color") and r < 50 and g < 150 and b > 100:
        return SIX_COLOR_PALETTE[4]

    input_lab = rgb_to_lab(r, g, b)
    min_dist = float("inf")
    closest = palette[0]
    for color in palette:
        color_lab = rgb_to_lab(color["r"], color["g"], color["b"])
        dist = lab_distance(input_lab, color_lab)
        if dist < min_dist:
            min_dist = dist
            closest = color
    return closest


# ============================================================
# 图像处理 - 亮度/对比度调整
# ============================================================

def adjust_brightness(pixels, width, height, factor):
    """调整图像亮度（原地修改）

    与 epdiy.cn 浏览器版 Gr() 保持一致:
      offset = (factor - 1) * 128
      factor=1.0 时不改变，>1 变亮，<1 变暗
    """
    offset = (factor - 1) * 128
    for i in range(width * height):
        idx = i * 4
        pixels[idx] = max(0, min(255, int(pixels[idx] + offset)))
        pixels[idx+1] = max(0, min(255, int(pixels[idx+1] + offset)))
        pixels[idx+2] = max(0, min(255, int(pixels[idx+2] + offset)))


def adjust_contrast(pixels, width, height, factor):
    """调整图像对比度（原地修改）"""
    for i in range(width * height):
        idx = i * 4
        pixels[idx] = max(0, min(255, int((pixels[idx] - 128) * factor + 128)))
        pixels[idx+1] = max(0, min(255, int((pixels[idx+1] - 128) * factor + 128)))
        pixels[idx+2] = max(0, min(255, int((pixels[idx+2] - 128) * factor + 128)))


# ============================================================
# 图像处理 - 抖动算法
# ============================================================

def _dither_floyd_steinberg(pixels, width, height, strength, mode):
    """Floyd-Steinberg 误差扩散抖动"""
    buf = list(pixels)
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            r, g, b = buf[idx], buf[idx+1], buf[idx+2]
            closest = find_closest_color(r, g, b, mode)
            er = (r - closest["r"]) * strength
            eg = (g - closest["g"]) * strength
            eb = (b - closest["b"]) * strength
            buf[idx] = closest["r"]
            buf[idx+1] = closest["g"]
            buf[idx+2] = closest["b"]
            for dx, dy, f in [(1,0,7/16),(-1,1,3/16),(0,1,5/16),(1,1,1/16)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height:
                    ni = (ny * width + nx) * 4
                    buf[ni] = max(0, min(255, int(buf[ni] + er * f)))
                    buf[ni+1] = max(0, min(255, int(buf[ni+1] + eg * f)))
                    buf[ni+2] = max(0, min(255, int(buf[ni+2] + eb * f)))
    for i in range(len(pixels)):
        if i % 4 < 3:
            pixels[i] = buf[i]


def _dither_atkinson(pixels, width, height, strength, mode):
    """Atkinson 误差扩散抖动"""
    buf = list(pixels)
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            r, g, b = buf[idx], buf[idx+1], buf[idx+2]
            closest = find_closest_color(r, g, b, mode)
            buf[idx] = closest["r"]
            buf[idx+1] = closest["g"]
            buf[idx+2] = closest["b"]
            er = (r - closest["r"]) * strength
            eg = (g - closest["g"]) * strength
            eb = (b - closest["b"]) * strength
            f = 1 / 8
            for dx, dy in [(1,0),(2,0),(-1,1),(0,1),(1,1),(0,2)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height:
                    ni = (ny * width + nx) * 4
                    buf[ni] = max(0, min(255, int(buf[ni] + er * f)))
                    buf[ni+1] = max(0, min(255, int(buf[ni+1] + eg * f)))
                    buf[ni+2] = max(0, min(255, int(buf[ni+2] + eb * f)))
    for i in range(len(pixels)):
        if i % 4 < 3:
            pixels[i] = buf[i]


def _dither_stucki(pixels, width, height, strength, mode):
    """Stucki 误差扩散抖动"""
    buf = list(pixels)
    kernel = [
        (1,0,8,42),(2,0,4,42),
        (-2,1,2,42),(-1,1,4,42),(0,1,8,42),(1,1,4,42),(2,1,2,42),
        (-2,2,1,42),(-1,2,2,42),(0,2,4,42),(1,2,2,42),(2,2,1,42),
    ]
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            r, g, b = buf[idx], buf[idx+1], buf[idx+2]
            closest = find_closest_color(r, g, b, mode)
            er = (r - closest["r"]) * strength
            eg = (g - closest["g"]) * strength
            eb = (b - closest["b"]) * strength
            buf[idx] = closest["r"]
            buf[idx+1] = closest["g"]
            buf[idx+2] = closest["b"]
            for dx, dy, num, den in kernel:
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height:
                    ni = (ny * width + nx) * 4
                    buf[ni] = max(0, min(255, int(buf[ni] + er * num / den)))
                    buf[ni+1] = max(0, min(255, int(buf[ni+1] + eg * num / den)))
                    buf[ni+2] = max(0, min(255, int(buf[ni+2] + eb * num / den)))
    for i in range(len(pixels)):
        if i % 4 < 3:
            pixels[i] = buf[i]


def _dither_jarvis(pixels, width, height, strength, mode):
    """Jarvis-Judice-Ninke 误差扩散抖动"""
    buf = list(pixels)
    kernel = [
        (1,0,7,48),(2,0,5,48),
        (-2,1,3,48),(-1,1,5,48),(0,1,7,48),(1,1,5,48),(2,1,3,48),
        (-2,2,1,48),(-1,2,3,48),(0,2,5,48),(1,2,3,48),(2,2,1,48),
    ]
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            r, g, b = buf[idx], buf[idx+1], buf[idx+2]
            closest = find_closest_color(r, g, b, mode)
            er = (r - closest["r"]) * strength
            eg = (g - closest["g"]) * strength
            eb = (b - closest["b"]) * strength
            buf[idx] = closest["r"]
            buf[idx+1] = closest["g"]
            buf[idx+2] = closest["b"]
            for dx, dy, num, den in kernel:
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height:
                    ni = (ny * width + nx) * 4
                    buf[ni] = max(0, min(255, int(buf[ni] + er * num / den)))
                    buf[ni+1] = max(0, min(255, int(buf[ni+1] + eg * num / den)))
                    buf[ni+2] = max(0, min(255, int(buf[ni+2] + eb * num / den)))
    for i in range(len(pixels)):
        if i % 4 < 3:
            pixels[i] = buf[i]


def _dither_bayer(pixels, width, height, strength, mode):
    """Bayer 有序抖动"""
    bayer8 = [
        [ 0,32, 8,40, 2,34,10,42],
        [48,16,56,24,50,18,58,26],
        [12,44, 4,36,14,46, 6,38],
        [60,28,52,20,62,30,54,22],
        [ 3,35,11,43, 1,33, 9,41],
        [51,19,59,27,49,17,57,25],
        [15,47, 7,39,13,45, 5,37],
        [63,31,55,23,61,29,53,21],
    ]
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            r, g, b = pixels[idx], pixels[idx+1], pixels[idx+2]
            threshold = (bayer8[y % 8][x % 8] / 64.0) * 255
            ar = max(0, min(255, int(r + (threshold - 127.5) * strength)))
            ag = max(0, min(255, int(g + (threshold - 127.5) * strength)))
            ab = max(0, min(255, int(b + (threshold - 127.5) * strength)))
            closest = find_closest_color(ar, ag, ab, mode)
            pixels[idx] = closest["r"]
            pixels[idx+1] = closest["g"]
            pixels[idx+2] = closest["b"]


DITHER_ALGORITHMS = {
    "floyd_steinberg": _dither_floyd_steinberg,
    "atkinson": _dither_atkinson,
    "stucki": _dither_stucki,
    "jarvis": _dither_jarvis,
    "bayer": _dither_bayer,
}


# ============================================================
# 图像处理 - 格式编码
# ============================================================

def process_image_bw(pixels, width, height):
    """黑白模式: 1bit per pixel, 阈值法"""
    byte_width = (width + 7) // 8
    result = bytearray(byte_width * height)
    threshold = 140
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            gray = int(0.299 * pixels[idx] + 0.587 * pixels[idx+1] + 0.114 * pixels[idx+2])
            if gray >= threshold:
                byte_idx = y * byte_width + x // 8
                result[byte_idx] |= (1 << (7 - (x % 8)))
    return bytes(result)


def process_image_3color(pixels, width, height):
    """三色模式: 黑白位图 + 红白位图"""
    byte_width = (width + 7) // 8
    bw_data = bytearray(byte_width * height)
    rw_data = bytearray(byte_width * height)
    bw_threshold = 140
    red_threshold = 160
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            r, g, b = pixels[idx], pixels[idx+1], pixels[idx+2]
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            if gray >= bw_threshold:
                bw_data[y * byte_width + x // 8] |= (1 << (7 - (x % 8)))
            if not (r > red_threshold and r > g and r > b):
                rw_data[y * byte_width + x // 8] |= (1 << (7 - (x % 8)))
    return bytes(bw_data + rw_data)


def process_image_3color_dithered(pixels, width, height):
    """三色模式(已抖动): 从抖动后的像素提取黑白+红白位图

    与 epdiy.cn 浏览器版 _t() 完全一致:
      - BW: luminance >= 140 → white(1), else → black(0)
      - RED: R > 160 && R > G && R > B → red(0), else → non-red(1)

    最终编码:
      - 白色: bw=1, rw=1  (RAM1=白, RAM2=非红)
      - 黑色: bw=0, rw=1  (RAM1=黑, RAM2=非红)
      - 红色: bw=0, rw=0  (RAM1=黑, RAM2=红)
    """
    byte_width = (width + 7) // 8
    bw_data = bytearray(byte_width * height)
    rw_data = bytearray(byte_width * height)
    bw_threshold = 140
    red_threshold = 160
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            r, g, b = pixels[idx], pixels[idx+1], pixels[idx+2]
            byte_idx = y * byte_width + x // 8
            bit = 1 << (7 - (x % 8))

            # BW: luminance >= 140 → white(1), else → black(0)
            luminance = round(0.299 * r + 0.587 * g + 0.114 * b)
            if luminance >= bw_threshold:
                bw_data[byte_idx] |= bit
            # else: black → bw 保持 0

            # RED: R > 160 && R > G && R > B → red(0), else → non-red(1)
            if not (r > red_threshold and r > g and r > b):
                rw_data[byte_idx] |= bit
            # else: red → rw 保持 0
    return bytes(bw_data + rw_data)


def process_image_4color(pixels, width, height):
    """四色模式: 2bit per pixel"""
    total = width * height
    result = bytearray((total + 3) // 4)
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            closest = find_closest_color(pixels[idx], pixels[idx+1], pixels[idx+2], "4color")
            val = closest["value"]
            new_idx = (y * width + x) // 4
            shift = 6 - ((x % 4) * 2)
            result[new_idx] |= (val << shift)
    return bytes(result)


def process_image_6color(pixels, width, height):
    """六色模式: 4bit per pixel"""
    total = width * height
    result = bytearray((total + 1) // 2)
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            closest = find_closest_color(pixels[idx], pixels[idx+1], pixels[idx+2], "6color")
            val = closest["value"]
            new_idx = (y * width + x) // 2
            if x % 2 == 0:
                result[new_idx] |= (val << 4)
            else:
                result[new_idx] |= val
    return bytes(result)


def convert_uc8159(bw_data, rw_data, pixel_count):
    """UC8159 驱动 IC 的三色数据转换"""
    result = bytearray(pixel_count * 4)
    idx = 0
    for i in range(pixel_count):
        byte_idx = i // 8
        bit_idx = 7 - (i % 8)
        black_bit = (bw_data[byte_idx] >> bit_idx) & 1 if byte_idx < len(bw_data) else 1
        color_bit = (rw_data[byte_idx] >> bit_idx) & 1 if byte_idx < len(rw_data) else 1
        if color_bit == 0:
            val = 0x04  # red
        elif black_bit == 0:
            val = 0x00  # black
        else:
            val = 0x03  # white
        if i % 2 == 0:
            result[idx] = (val << 4) & 0xFF
        else:
            result[idx] |= val
            idx += 1
    return bytes(result[:idx + (1 if pixel_count % 2 else 0)])


# ============================================================
# 图像处理 - 主入口
# ============================================================

def _fit_image(img: Image.Image, width: int, height: int, fit: str) -> Image.Image:
    """将图片适配到目标尺寸

    Args:
        img: PIL Image 对象
        width: 目标宽度
        height: 目标高度
        fit: 适配模式
            - stretch: 拉伸填充（可能变形）
            - contain: 等比缩放，保留完整图片，留白填充
            - cover: 等比缩放并裁剪，铺满整个屏幕

    Returns:
        适配后的 PIL Image 对象
    """
    if fit == "stretch":
        return img.resize((width, height), Image.LANCZOS)

    src_w, src_h = img.size
    src_ratio = src_w / src_h
    dst_ratio = width / height

    if fit == "contain":
        # 等比缩放，使图片完整显示在屏幕内，用白色填充剩余区域
        if src_ratio > dst_ratio:
            new_w = width
            new_h = max(1, round(width / src_ratio))
        else:
            new_h = height
            new_w = max(1, round(height * src_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
        paste_x = (width - new_w) // 2
        paste_y = (height - new_h) // 2
        canvas.paste(resized, (paste_x, paste_y))
        return canvas

    elif fit == "cover":
        # 等比缩放，使图片铺满整个屏幕，居中裁剪多余部分
        if src_ratio > dst_ratio:
            # 图片更宽，裁剪两侧
            new_h = height
            new_w = max(1, round(height * src_ratio))
        else:
            # 图片更高，裁剪上下
            new_w = width
            new_h = max(1, round(width / src_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        crop_x = (new_w - width) // 2
        crop_y = (new_h - height) // 2
        return resized.crop((crop_x, crop_y, crop_x + width, crop_y + height))

    else:
        raise ValueError(f"不支持的适配模式: {fit}，可选: stretch/contain/cover")


def load_and_process_image(
    image_path: str,
    width: int,
    height: int,
    mode: str = "bw",
    dither: str = "floyd_steinberg",
    strength: float = 1.0,
    contrast: float = 1.2,
    brightness: float = 1.0,
    fit: str = "stretch",
    return_pixels: bool = False,
):
    """加载图片并处理为 EPD 数据格式

    Args:
        return_pixels: 为 True 时额外返回抖动后的像素数据（用于预览）
    """
    img = Image.open(image_path).convert("RGBA")
    img = _fit_image(img, width, height, fit)

    raw = list(img.convert("RGB").tobytes())
    pixel_count = width * height
    pixels = [0] * (pixel_count * 4)
    for i in range(pixel_count):
        pixels[i*4] = raw[i*3]
        pixels[i*4+1] = raw[i*3+1]
        pixels[i*4+2] = raw[i*3+2]
        pixels[i*4+3] = 255

    if brightness != 1.0:
        adjust_brightness(pixels, width, height, brightness)

    if contrast != 1.0:
        adjust_contrast(pixels, width, height, contrast)

    if dither != "none" and dither in DITHER_ALGORITHMS:
        DITHER_ALGORITHMS[dither](pixels, width, height, strength, mode)

    if mode == "bw":
        data = process_image_bw(pixels, width, height)
    elif mode == "3color":
        data = process_image_3color_dithered(pixels, width, height)
    elif mode == "4color":
        data = process_image_4color(pixels, width, height)
    elif mode == "6color":
        data = process_image_6color(pixels, width, height)
    else:
        raise ValueError(f"不支持的颜色模式: {mode}")

    if return_pixels:
        return data, pixels
    return data


def _pixels_to_preview_image(pixels: list, width: int, height: int, mode: str) -> Image.Image:
    """将处理后的像素数据转换为可预览的 PIL Image"""
    img = Image.new("RGB", (width, height))
    img_data = []
    for i in range(width * height):
        idx = i * 4
        img_data.append((pixels[idx], pixels[idx + 1], pixels[idx + 2]))
    img.putdata(img_data)
    return img


def _generate_dry_run_preview(
    image_path: str,
    width: int,
    height: int,
    mode: str,
    dither: str,
    strength: float,
    contrast: float,
    brightness: float,
    fit: str,
    output: Optional[str],
) -> dict:
    """dry-run 模式：处理图片并保存预览，不发送到设备"""
    start = time.time()
    _, pixels = load_and_process_image(
        image_path, width, height, mode, dither, strength, contrast, brightness, fit,
        return_pixels=True,
    )
    process_time = time.time() - start

    preview = _pixels_to_preview_image(pixels, width, height, mode)

    if output is None:
        p = Path(image_path)
        output = str(p.with_stem(p.stem + "_preview").with_suffix(".png"))

    preview.save(output)
    return {
        "dry_run": True,
        "model_size": f"{width}x{height}",
        "mode": mode,
        "dither": dither,
        "fit": fit,
        "process_time": f"{process_time:.2f}s",
        "output": output,
    }


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
            timezone = -int(time.timezone // 3600) if time.daylight == 0 else -int(time.altzone // 3600)
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
    import platform
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
    import platform
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
        import platform
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
# 配置持久化（地址记忆）
# ============================================================

CONFIG_DIR = Path.home() / ".config" / "epd-tool"
CONFIG_FILE = CONFIG_DIR / "config.json"


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


def _warn_macos_adapter(adapter: Optional[str]) -> None:
    """在 macOS 上提示用户 adapter 参数无效"""
    if adapter:
        import platform
        if platform.system() == "Darwin":
            typer.echo(
                f"警告: macOS CoreBluetooth 不支持指定蓝牙适配器，--adapter {adapter} 将被忽略。",
                err=True,
            )


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
            # Linux BLE栈对连续写入操作更敏感，需要确保前一个命令完成后再发送下一个
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
                await asyncio.sleep(2.0)  # 更长的重试间隔
                result = await client.set_slot(mode=1, slot_id=slot_id)
                if not json_output:
                    typer.echo("SET_SLOT命令重试成功")
            
            # 等待设备处理SET_SLOT命令（Linux需要更长的间隔）
            await asyncio.sleep(1.5)
            
            # 步骤2: 发送 SET_TIME(mode=0/PICTURE) 强制触发 GUI 更新
            # 固件的 SET_TIME 处理会调用 ble_epd_on_timer(force_update=true)
            # 这会触发 epd_gui_update → DrawGUI(MODE_PICTURE) → 加载槽位图片 → refresh
            if not json_output:
                typer.echo(f"正在显示槽位 {slot_id}，请等待屏幕刷新...")
            
            try:
                await client.set_time(mode=0)  # mode=0 即 MODE_PICTURE
            except Exception as e:
                # Linux上可能出现GATT协议错误，重试一次
                if not json_output:
                    typer.echo(f"SET_TIME命令失败，正在重试... ({e})", err=True)
                await asyncio.sleep(1.0)
                await client.set_time(mode=0)
            
            # 等待固件内部 GUI 更新完成（加载图片 + 刷新屏幕）
            # epd_gui_update 包含: write_image + refresh + sleep，约需 10-15 秒
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
    import platform
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


# ============================================================
# 入口
# ============================================================

def main():
    try:
        app()
    except KeyboardInterrupt:
        typer.echo("\n已取消")
    except Exception as e:
        typer.echo(f"错误: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
