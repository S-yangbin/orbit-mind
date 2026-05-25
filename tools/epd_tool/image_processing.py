"""
EPD-nRF5 图像处理

包含颜色空间转换、抖动算法、图像编码、预览生成等功能。
"""

import math
import time
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError:
    import typer
    typer.echo("错误: 需要安装 Pillow 库。请运行: pip install Pillow", err=True)
    raise SystemExit(1)

from .constants import SIX_COLOR_PALETTE, FOUR_COLOR_PALETTE, THREE_COLOR_PALETTE, EPD_MODELS


# ============================================================
# 颜色空间与调色板
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
# 亮度/对比度调整
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
# 抖动算法
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
# 图像格式编码
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
