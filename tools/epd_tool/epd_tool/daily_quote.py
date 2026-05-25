"""
EPD-nRF5 每日箴言图片生成

包含箴言获取、天气查询、纹理绘制、图片合成等功能。
"""

import json
import os
import urllib.parse
import urllib.request
from typing import Optional


# ============================================================
# 内置箴言库（网络不可用时 fallback）
# ============================================================

BUILT_IN_QUOTES = [
    "知行合一，止于至善。",
    "博学之，审问之，慎思之，明辨之，笃行之。",
    "天行健，君子以自强不息。",
    "地势坤，君子以厚德载物。",
    "不积跬步，无以至千里。",
    "千里之行，始于足下。",
    "学而不思则罔，思而不学则殆。",
    "知者不惑，仁者不忧，勇者不惧。",
    "上善若水，水善利万物而不争。",
    "大道至简，衍化至繁。",
    "静以修身，俭以养德。",
    "非淡泊无以明志，非宁静无以致远。",
    "业精于勤，荒于嬉；行成于思，毁于随。",
    "海纳百川，有容乃大；壁立千仞，无欲则刚。",
    "岁寒，然后知松柏之后凋也。",
    "三人行，必有我师焉。",
    "温故而知新，可以为师矣。",
    "己所不欲，勿施于人。",
    "敏而好学，不耻下问。",
    "生当作人杰，死亦为鬼雄。",
    "路漫漫其修远兮，吾将上下而求索。",
    "人法地，地法天，天法道，道法自然。",
    "工欲善其事，必先利其器。",
    "玉不琢，不成器；人不学，不知道。",
    "知人者智，自知者明。",
    "祸兮福之所倚，福兮祸之所伏。",
    "合抱之木，生于毫末；九层之台，起于累土。",
    "士不可以不弘毅，任重而道远。",
    "穷则独善其身，达则兼济天下。",
    "莫愁前路无知己，天下谁人不识君。",
    "长风破浪会有时，直挂云帆济沧海。",
]

_WEEKDAYS_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
_WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# 天气图标 (用简单字符表示)
_WEATHER_ICONS = {
    "晴": "☀",
    "多云": "⛅",
    "阴": "☁",
    "小雨": "🌦",
    "雨": "☂",
    "大雨": "☂",
    "雷阵雨": "⛈",
    "雪": "❄",
    "雾": "≡",
    "霾": "≡",
}


# ============================================================
# 箴言与天气获取
# ============================================================

def _fetch_hitokoto() -> Optional[str]:
    """从一言 API (hitokoto.cn) 随机获取一条箴言"""
    try:
        url = "https://v1.hitokoto.cn/"
        req = urllib.request.Request(url, headers={"User-Agent": "epd-tool/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            hitokoto = data.get("hitokoto", "").strip()
            if hitokoto:
                # 若有出处，附加来源
                source = data.get("from", "").strip()
                if source:
                    return f"{hitokoto} —— {source}"
                return hitokoto
    except Exception:
        pass
    return None


def _pick_quote() -> str:
    """获取今日箴言：优先从 hitokoto.cn 在线拉取，失败则 fallback 到内置箴言库"""
    import datetime

    online_quote = _fetch_hitokoto()
    if online_quote:
        return online_quote

    # fallback: 基于日期选择内置箴言（同一天总是同一条）
    day_of_year = datetime.datetime.now().timetuple().tm_yday
    return BUILT_IN_QUOTES[day_of_year % len(BUILT_IN_QUOTES)]


def _find_cjk_font():
    """查找系统中可用的中文字体"""
    import platform
    candidates = []
    system = platform.system()
    if system == "Darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
    elif system == "Linux":
        candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ]
    else:  # Windows
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
        ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _fetch_weather(city: str) -> Optional[dict]:
    """从 wttr.in 获取天气信息"""
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        current = data.get("current_condition", [{}])[0]
        desc_list = current.get("lang_zh", [{}])
        desc = desc_list[0].get("value", current.get("weatherDesc", [{}])[0].get("value", "")) if desc_list else ""
        temp_c = current.get("temp_C", "")
        humidity = current.get("humidity", "")
        return {"desc": desc, "temp": temp_c, "humidity": humidity}
    except Exception:
        return None


# ============================================================
# 文本工具
# ============================================================

def _wrap_text(text: str, font, max_width: int, draw) -> list:
    """将文本按最大宽度换行"""
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_width:
            if current_line:
                lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return lines


# ============================================================
# 天气纹理背景
# ============================================================

# 天气描述中文关键词 → 纹理类型映射
_WEATHER_TEXTURE_MAP = {
    # 晴天类
    "晴": "sunny", "晴朗": "sunny", "大晴": "sunny", "clear": "sunny",
    # 多云类
    "多云": "cloudy", "阴": "cloudy", "阴天": "cloudy", "overcast": "cloudy",
    "局部多云": "cloudy", "大部多云": "cloudy",
    # 雨类
    "小雨": "rain_light", "中雨": "rain", "大雨": "rain_heavy",
    "雨": "rain", "阵雨": "rain", "毛毛雨": "rain_light",
    "间歇雨": "rain", "暴雨": "rain_heavy", "雷阵雨": "thunderstorm",
    "雷雨": "thunderstorm",
    # 雪类
    "小雪": "snow", "中雪": "snow", "大雪": "snow_heavy",
    "雪": "snow", "暴雪": "snow_heavy",
    # 雾类
    "雾": "fog", "薄雾": "fog", "浓雾": "fog",
    # 风/沙类
    "大风": "wind", "沙尘": "wind", "霾": "fog",
}


def _classify_weather_texture(weather_desc: str) -> str:
    """根据中文天气描述判断应绘制哪种纹理类型"""
    if not weather_desc:
        return "default"
    # 逐词匹配（中文天气描述可能包含多个关键词）
    for keyword, texture_type in _WEATHER_TEXTURE_MAP.items():
        if keyword in weather_desc:
            return texture_type
    return "default"


def _draw_texture_sunny(draw, width, height, banner_h, margin):
    """晴天纹理：从左上角辐射出的光束条纹 + 光晕区域"""
    # 三色化阈值=140, 灰度<140→黑, >=140→白
    # 用接近阈值的灰度让纹理在原始PNG中微妙但在三色化后明显
    DARK_GRAY = (135, 135, 135)   # 灰度≈135, 三色化后→黑 (核心光线)
    MED_GRAY = (155, 155, 155)   # 灰度≈155, 三色化后→黑 (次要光线)
    LIGHT_GRAY = (175, 175, 175) # 灰度≈175, 三色化后→黑 (柔光边缘)
    RED_ACCENT = (200, 30, 30)

    # 光束: 从左上辐射的对角线条纹 (加粗加密)
    num_beams = 8
    cx, cy = margin, banner_h + 6
    import random
    rng = random.Random(42)
    for i in range(num_beams):
        angle_offset = i * 6
        x_end = cx + 50 + angle_offset * 5
        y_end = cy + 70 + angle_offset * 3
        # 核心光线 (暗灰/黑)
        draw.line([(cx, cy), (x_end, y_end)], fill=DARK_GRAY, width=2)
        # 柔光边缘
        draw.line([(cx + 2, cy), (x_end + 2, y_end)], fill=MED_GRAY, width=1)
        draw.line([(cx - 2, cy), (x_end - 2, y_end)], fill=LIGHT_GRAY, width=1)

    # 左上角光晕圆弧
    draw.arc([(margin - 10, banner_h + 2), (margin + 30, banner_h + 30)], 200, 340, fill=DARK_GRAY, width=2)

    # 散布红色光点 (更大更明显)
    for _ in range(10):
        px = rng.randint(width // 3, width - margin)
        py = rng.randint(height // 2, height - banner_h - margin)
        r = 2
        draw.ellipse([(px - r, py - r), (px + r, py + r)], fill=RED_ACCENT)


def _draw_texture_rain_light(draw, width, height, banner_h, margin):
    """小雨纹理：稀疏的斜雨丝"""
    DARK_GRAY = (135, 135, 135)   # 三色化后→黑
    MED_GRAY = (155, 155, 155)   # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 斜线 (从右上到左下) - 加宽加长
    num_lines = 20
    for _ in range(num_lines):
        x1 = rng.randint(margin, width - margin)
        y1 = rng.randint(banner_h + 10, height // 2)
        length = rng.randint(20, 40)
        color = DARK_GRAY if rng.random() > 0.5 else MED_GRAY
        draw.line([(x1, y1), (x1 - length // 2, y1 + length)], fill=color, width=1)

    # 底部红色水滴 (更大)
    for _ in range(5):
        dx = rng.randint(margin + 20, width - margin - 20)
        dy = rng.randint(height - banner_h - 30, height - banner_h - 10)
        r = 3
        draw.ellipse([(dx - r, dy - r), (dx + r, dy)], fill=RED_ACCENT)


def _draw_texture_rain(draw, width, height, banner_h, margin):
    """中雨纹理：密集斜雨丝"""
    DARK_GRAY = (135, 135, 135)   # 三色化后→黑
    VERY_DARK = (110, 110, 110)  # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 密集斜线
    num_lines = 40
    for _ in range(num_lines):
        x1 = rng.randint(margin // 2, width)
        y1 = rng.randint(banner_h, height - banner_h)
        length = rng.randint(25, 50)
        x2 = x1 - length // 3
        y2 = y1 + length
        color = DARK_GRAY if rng.random() > 0.3 else VERY_DARK
        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

    # 底部红色水滴 (更多更大)
    for _ in range(8):
        dx = rng.randint(margin + 10, width - margin - 10)
        dy = rng.randint(height - banner_h - 25, height - banner_h - 5)
        r = 3
        draw.ellipse([(dx - r, dy - r), (dx + r, dy)], fill=RED_ACCENT)


def _draw_texture_rain_heavy(draw, width, height, banner_h, margin):
    """大雨纹理：非常密集的雨丝 + 水滴"""
    VERY_DARK = (110, 110, 110)  # 三色化后→黑
    DARK_GRAY = (130, 130, 130)  # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 极密集斜线 (覆盖整个画面)
    num_lines = 60
    for _ in range(num_lines):
        x1 = rng.randint(0, width)
        y1 = rng.randint(banner_h, height - banner_h)
        length = rng.randint(30, 60)
        x2 = x1 - length // 3
        y2 = y1 + length
        color = DARK_GRAY if rng.random() > 0.4 else VERY_DARK
        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

    # 大水滴
    for _ in range(10):
        dx = rng.randint(margin, width - margin)
        dy = rng.randint(height - banner_h - 20, height - banner_h)
        r = 4
        draw.ellipse([(dx - r, dy - r), (dx + r, dy)], fill=RED_ACCENT)


def _draw_texture_thunderstorm(draw, width, height, banner_h, margin):
    """雷雨纹理：雨丝 + 闪电折线"""
    DARK_GRAY = (130, 130, 130)  # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 密集雨丝
    num_lines = 40
    for _ in range(num_lines):
        x1 = rng.randint(0, width)
        y1 = rng.randint(banner_h, height - banner_h)
        length = rng.randint(25, 50)
        x2 = x1 - length // 3
        y2 = y1 + length
        draw.line([(x1, y1), (x2, y2)], fill=DARK_GRAY, width=1)

    # 闪电: 红色锯齿折线 (加宽加长)
    lx = width // 2 + rng.randint(-30, 30)
    ly = banner_h + 15
    bolt_points = [(lx, ly)]
    for _ in range(7):
        lx += rng.randint(-15, 15)
        ly += rng.randint(8, 20)
        bolt_points.append((lx, ly))
    for i in range(len(bolt_points) - 1):
        draw.line([bolt_points[i], bolt_points[i + 1]], fill=RED_ACCENT, width=3)

    # 水滴
    for _ in range(6):
        dx = rng.randint(margin, width - margin)
        dy = rng.randint(height - banner_h - 20, height - banner_h)
        draw.ellipse([(dx - 3, dy - 3), (dx + 3, dy)], fill=RED_ACCENT)


def _draw_texture_snow(draw, width, height, banner_h, margin):
    """雪天纹理：散布的雪花小图案"""
    DARK_GRAY = (135, 135, 135)  # 三色化后→黑
    MED_GRAY = (155, 155, 155)   # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 雪花: 十字 + 对角线组成的小六瓣花 (更大)
    num_flakes = 22
    for _ in range(num_flakes):
        cx = rng.randint(margin + 10, width - margin - 10)
        cy = rng.randint(banner_h + 10, height - banner_h - 10)
        s = rng.randint(4, 8)  # 雪花半径
        color = DARK_GRAY if rng.random() > 0.5 else MED_GRAY
        # 六瓣: 三条交叉线
        draw.line([(cx - s, cy), (cx + s, cy)], fill=color, width=1)  # 横
        draw.line([(cx, cy - s), (cx, cy + s)], fill=color, width=1)  # 竖
        draw.line([(cx - s, cy - s), (cx + s, cy + s)], fill=color, width=1)  # 斜1
        draw.line([(cx - s, cy + s), (cx + s, cy - s)], fill=color, width=1)  # 斜2

    # 几个红色小圆点缀
    for _ in range(6):
        px = rng.randint(margin + 20, width - margin - 20)
        py = rng.randint(height - banner_h - 20, height - banner_h - 5)
        draw.ellipse([(px - 2, py - 2), (px + 2, py + 2)], fill=RED_ACCENT)


def _draw_texture_snow_heavy(draw, width, height, banner_h, margin):
    """大雪纹理：更多更大的雪花"""
    DARK_GRAY = (130, 130, 130)  # 三色化后→黑
    VERY_DARK = (110, 110, 110)  # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 大量雪花 (更大更多)
    num_flakes = 35
    for _ in range(num_flakes):
        cx = rng.randint(margin, width - margin)
        cy = rng.randint(banner_h, height - banner_h)
        s = rng.randint(5, 10)
        color = DARK_GRAY if rng.random() > 0.4 else VERY_DARK
        draw.line([(cx - s, cy), (cx + s, cy)], fill=color, width=1)
        draw.line([(cx, cy - s), (cx, cy + s)], fill=color, width=1)
        draw.line([(cx - s, cy - s), (cx + s, cy + s)], fill=color, width=1)
        draw.line([(cx - s, cy + s), (cx + s, cy - s)], fill=color, width=1)

    # 红色点缀
    for _ in range(8):
        px = rng.randint(margin, width - margin)
        py = rng.randint(height - banner_h - 25, height - banner_h)
        draw.ellipse([(px - 2, py - 2), (px + 2, py + 2)], fill=RED_ACCENT)


def _draw_texture_cloudy(draw, width, height, banner_h, margin):
    """多云/阴天纹理：横向云带波纹"""
    DARK_GRAY = (130, 130, 130)  # 三色化后→黑
    MED_GRAY = (145, 145, 145)   # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 几条横贯画面的波浪形云带 (加粗加密)
    num_bands = 5
    band_spacing = (height - 2 * banner_h) // (num_bands + 1)
    for i in range(num_bands):
        y_base = banner_h + band_spacing * (i + 1)
        # 用弧线段拼出波浪
        segments = 8
        seg_w = width // segments
        for j in range(segments):
            x_start = j * seg_w
            x_end = x_start + seg_w
            amplitude = rng.randint(6, 14)
            y_offset = rng.randint(-4, 4)
            draw.arc(
                [(x_start, y_base + y_offset - amplitude),
                 (x_end, y_base + y_offset + amplitude)],
                0, 180,
                fill=DARK_GRAY if i % 2 == 0 else MED_GRAY,
                width=2,
            )

    # 两侧红色小点缀
    draw.ellipse([(margin + 3, banner_h + 12), (margin + 11, banner_h + 22)], fill=RED_ACCENT)
    draw.ellipse([(width - margin - 11, banner_h + 12), (width - margin - 3, banner_h + 22)], fill=RED_ACCENT)


def _draw_texture_fog(draw, width, height, banner_h, margin):
    """雾天纹理：水平渐隐条纹"""
    DARK_GRAY = (130, 130, 130)  # 三色化后→黑
    MED_GRAY = (150, 150, 150)   # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 水平条纹 (更粗更密)
    num_lines = 8
    spacing = (height - 2 * banner_h) // (num_lines + 1)
    for i in range(num_lines):
        y = banner_h + spacing * (i + 1)
        # 用连续线段代替虚线
        color = DARK_GRAY if i % 2 == 0 else MED_GRAY
        draw.line([(margin, y), (width - margin, y)], fill=color, width=1)

    # 红色点缀
    draw.ellipse([(width // 2 - 3, banner_h + 18), (width // 2 + 3, banner_h + 24)], fill=RED_ACCENT)

    # 红色点缀
    draw.ellipse([(width // 2 - 2, banner_h + 20), (width // 2 + 2, banner_h + 24)], fill=RED_ACCENT)


def _draw_texture_wind(draw, width, height, banner_h, margin):
    """大风纹理：横向飘动曲线"""
    DARK_GRAY = (130, 130, 130)  # 三色化后→黑
    MED_GRAY = (145, 145, 145)   # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 风线: S形曲线 (更长更密)
    num_lines = 14
    for _ in range(num_lines):
        y_base = rng.randint(banner_h + 10, height - banner_h - 10)
        points = []
        x = margin // 2
        while x < width - margin // 2:
            dx = rng.randint(25, 50)
            dy = rng.randint(-8, 8)
            points.append((x, y_base + dy))
            x += dx
        if len(points) >= 2:
            for j in range(len(points) - 1):
                color = DARK_GRAY if rng.random() > 0.3 else MED_GRAY
                draw.line([points[j], points[j + 1]], fill=color, width=2)

    # 红色风点 (更大)
    for _ in range(6):
        px = rng.randint(margin, width - margin)
        py = rng.randint(banner_h + 20, height - banner_h - 20)
        draw.ellipse([(px - 2, py - 2), (px + 2, py + 2)], fill=RED_ACCENT)


def _draw_texture_default(draw, width, height, banner_h, margin):
    """默认纹理：极淡的几何点缀（无明显天气特征时使用）"""
    DARK_GRAY = (130, 130, 130)  # 三色化后→黑
    MED_GRAY = (145, 145, 145)   # 三色化后→黑
    RED_ACCENT = (200, 30, 30)
    import random
    rng = random.Random(42)

    # 随机散布几个小菱形 (更多更大)
    for _ in range(10):
        cx = rng.randint(margin + 20, width - margin - 20)
        cy = rng.randint(banner_h + 20, height - banner_h - 20)
        d = 4
        color = DARK_GRAY if rng.random() > 0.5 else MED_GRAY
        draw.polygon([(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)], fill=color)

    # 两个红色小点
    draw.ellipse([(width // 3 - 2, banner_h + 12), (width // 3 + 2, banner_h + 18)], fill=RED_ACCENT)
    draw.ellipse([(2 * width // 3 - 2, banner_h + 12), (2 * width // 3 + 2, banner_h + 18)], fill=RED_ACCENT)


_TEXTURE_DRAWERS = {
    "sunny": _draw_texture_sunny,
    "rain_light": _draw_texture_rain_light,
    "rain": _draw_texture_rain,
    "rain_heavy": _draw_texture_rain_heavy,
    "thunderstorm": _draw_texture_thunderstorm,
    "snow": _draw_texture_snow,
    "snow_heavy": _draw_texture_snow_heavy,
    "cloudy": _draw_texture_cloudy,
    "fog": _draw_texture_fog,
    "wind": _draw_texture_wind,
    "default": _draw_texture_default,
}


# ============================================================
# 装饰元素绘制
# ============================================================

def _draw_decorative_border(draw, x, y, w, h, color):
    """绘制装饰性双线边框"""
    draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
    inset = 5
    draw.rectangle([x + inset, y + inset, x + w - inset, y + h - inset], outline=color, width=1)


def _draw_corner_flower(draw, x, y, size, color, corner="tl"):
    """绘制角落花纹装饰（L 形折线 + 小圆点）"""
    s = size
    r = max(2, size // 6)
    if corner == "tl":
        draw.line([(x, y), (x + s, y)], fill=color, width=2)
        draw.line([(x, y), (x, y + s)], fill=color, width=2)
        draw.line([(x + 3, y + 3), (x + s - 4, y + 3)], fill=color, width=1)
        draw.line([(x + 3, y + 3), (x + 3, y + s - 4)], fill=color, width=1)
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)
    elif corner == "tr":
        draw.line([(x - s, y), (x, y)], fill=color, width=2)
        draw.line([(x, y), (x, y + s)], fill=color, width=2)
        draw.line([(x - 3, y + 3), (x - s + 4, y + 3)], fill=color, width=1)
        draw.line([(x - 3, y + 3), (x - 3, y + s - 4)], fill=color, width=1)
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)
    elif corner == "bl":
        draw.line([(x, y - s), (x, y)], fill=color, width=2)
        draw.line([(x, y), (x + s, y)], fill=color, width=2)
        draw.line([(x + 3, y - 3), (x + s - 4, y - 3)], fill=color, width=1)
        draw.line([(x + 3, y - 3), (x + 3, y - s + 4)], fill=color, width=1)
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)
    elif corner == "br":
        draw.line([(x, y - s), (x, y)], fill=color, width=2)
        draw.line([(x - s, y), (x, y)], fill=color, width=2)
        draw.line([(x - 3, y - 3), (x - s + 4, y - 3)], fill=color, width=1)
        draw.line([(x - 3, y - 3), (x - 3, y - s + 4)], fill=color, width=1)
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)


def _draw_cloud_pattern(draw, cx, cy, size, color):
    """绘制中式祥云纹样"""
    r = size
    # 三个交叠圆弧组成祥云
    draw.arc([(cx - r, cy - r), (cx + r, cy + r)], 200, 340, fill=color, width=1)
    draw.arc([(cx + r // 2 - r, cy - r // 2), (cx + r // 2 + r, cy + r // 2 + r)], 180, 320, fill=color, width=1)
    draw.arc([(cx - r // 2 - r, cy - r // 2), (cx - r // 2 + r, cy + r // 2 + r)], 220, 360, fill=color, width=1)


def _draw_decorative_divider(draw, cx, cy, width, color_accent, color_main):
    """绘制装饰分隔线：——◆—— 样式"""
    half = width // 2
    # 左右线段
    draw.line([(cx - half, cy), (cx - 6, cy)], fill=color_main, width=1)
    draw.line([(cx + 6, cy), (cx + half, cy)], fill=color_main, width=1)
    # 中间菱形
    d = 4
    draw.polygon([(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)], fill=color_accent)
    # 两端小圆点
    draw.ellipse([(cx - half - 2, cy - 2), (cx - half + 2, cy + 2)], fill=color_accent)
    draw.ellipse([(cx + half - 2, cy - 2), (cx + half + 2, cy + 2)], fill=color_accent)


# ============================================================
# 主图片生成函数
# ============================================================

def generate_daily_quote_image(
    width: int, height: int,
    date_str: str, weekday: str,
    weather_text: str,
    quote_text: str,
    font_path: Optional[str],
    output_path: str,
    weekday_en: str = "",
    weather_desc_raw: str = "",  # 原始天气描述，用于纹理分类
) -> dict:
    """生成每日箴言图片"""
    from PIL import Image, ImageDraw, ImageFont

    # 颜色定义: 红、白、黑
    RED = (200, 30, 30)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (160, 160, 160)

    # 创建白色背景图片
    img = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(img)

    # 加载字体
    if font_path and os.path.exists(font_path):
        actual_font_path = font_path
    else:
        actual_font_path = _find_cjk_font()

    def get_font(size):
        if actual_font_path:
            try:
                return ImageFont.truetype(actual_font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    # 字体大小层次
    font_weekday_en = get_font(max(14, width // 26))   # 英文星期（小）
    font_weekday_zh = get_font(max(26, width // 13))   # 中文星期（大字）
    font_date = get_font(max(15, width // 24))          # 日期
    font_weather = get_font(max(13, width // 28))       # 天气
    font_quote = get_font(max(18, width // 18))         # 箴言正文
    font_quote_mark = get_font(max(32, width // 10))    # 引号装饰
    font_small = get_font(max(10, width // 36))         # 辅助小字

    margin = max(16, width // 20)

    # ─── 天气纹理背景 ───
    texture_type = _classify_weather_texture(weather_desc_raw)
    banner_h_val = max(10, height // 30)
    margin_val = max(16, width // 20)
    texture_func = _TEXTURE_DRAWERS.get(texture_type, _draw_texture_default)
    if texture_func:
        texture_func(draw, width, height, banner_h_val, margin_val)

    # ─── 顶部红色装饰条幅（渐变模拟） ───
    banner_h = max(10, height // 30)
    draw.rectangle([0, 0, width, banner_h], fill=RED)
    # 条幅底部锯齿纹
    tooth_w = max(6, width // 50)
    for tx in range(0, width, tooth_w * 2):
        draw.polygon(
            [(tx, banner_h), (tx + tooth_w, banner_h + 4), (tx + tooth_w * 2, banner_h)],
            fill=RED,
        )

    # ─── 底部红色装饰条幅 ───
    draw.rectangle([0, height - banner_h, width, height], fill=RED)
    # 条幅顶部锯齿纹
    for tx in range(0, width, tooth_w * 2):
        draw.polygon(
            [(tx, height - banner_h), (tx + tooth_w, height - banner_h - 4), (tx + tooth_w * 2, height - banner_h)],
            fill=RED,
        )

    # ─── 装饰性双线边框 ───
    border_margin = margin // 2 + 2
    _draw_decorative_border(
        draw, border_margin, banner_h + 6 + border_margin,
        width - 2 * border_margin, height - 2 * banner_h - 12 - 2 * border_margin,
        BLACK,
    )

    # ─── 角落花纹装饰 ───
    orn_size = max(16, width // 20)
    ix1 = border_margin + 7
    iy1 = banner_h + 6 + border_margin + 7
    ix2 = width - border_margin - 7
    iy2 = height - banner_h - 6 - border_margin - 7
    _draw_corner_flower(draw, ix1, iy1, orn_size, RED, "tl")
    _draw_corner_flower(draw, ix2, iy1, orn_size, RED, "tr")
    _draw_corner_flower(draw, ix1, iy2, orn_size, RED, "bl")
    _draw_corner_flower(draw, ix2, iy2, orn_size, RED, "br")

    # ─── 左右祥云纹样 ───
    cloud_size = max(6, width // 50)
    _draw_cloud_pattern(draw, ix1 + orn_size // 2 + cloud_size + 4, iy1 + 2, cloud_size, GRAY)
    _draw_cloud_pattern(draw, ix2 - orn_size // 2 - cloud_size - 4, iy1 + 2, cloud_size, GRAY)

    # ═══ 内容区域 ═══
    y_cursor = banner_h + margin + 12

    # --- 英文星期（小号灰色） ---
    if weekday_en:
        en_bbox = draw.textbbox((0, 0), weekday_en.upper(), font=font_weekday_en)
        en_w = en_bbox[2] - en_bbox[0]
        draw.text(((width - en_w) // 2, y_cursor), weekday_en.upper(), fill=GRAY, font=font_weekday_en)
        y_cursor += (en_bbox[3] - en_bbox[1]) + 2

    # --- 中文星期（大字黑色） ---
    zh_bbox = draw.textbbox((0, 0), weekday, font=font_weekday_zh)
    zh_w = zh_bbox[2] - zh_bbox[0]
    draw.text(((width - zh_w) // 2, y_cursor), weekday, fill=BLACK, font=font_weekday_zh)
    y_cursor += (zh_bbox[3] - zh_bbox[1]) + 6

    # --- 日期（红色） ---
    date_bbox = draw.textbbox((0, 0), date_str, font=font_date)
    date_w = date_bbox[2] - date_bbox[0]
    draw.text(((width - date_w) // 2, y_cursor), date_str, fill=RED, font=font_date)
    y_cursor += (date_bbox[3] - date_bbox[1]) + 10

    # --- 装饰分隔线 ---
    div_w = min(width // 3, 120)
    _draw_decorative_divider(draw, width // 2, y_cursor, div_w, RED, BLACK)
    y_cursor += 14

    # --- 天气 ---
    if weather_text:
        weather_bbox = draw.textbbox((0, 0), weather_text, font=font_weather)
        weather_w = weather_bbox[2] - weather_bbox[0]
        draw.text(((width - weather_w) // 2, y_cursor), weather_text, fill=BLACK, font=font_weather)
        y_cursor += (weather_bbox[3] - weather_bbox[1]) + 10

    # ═══ 箴言区域（居中） ═══
    quote_area_width = width - 2 * (margin + 24)
    quote_lines = _wrap_text(quote_text, font_quote, quote_area_width, draw)

    line_height = (font_quote.size + 10) if hasattr(font_quote, 'size') else 32
    quote_total_h = len(quote_lines) * line_height
    available_h = height - banner_h * 2 - y_cursor - margin - 24
    quote_start_y = y_cursor + max(8, available_h // 2 - quote_total_h // 2)

    # 左引号
    draw.text((margin + 14, quote_start_y - 20), "\u201c", fill=RED, font=font_quote_mark)

    for i, line in enumerate(quote_lines):
        line_bbox = draw.textbbox((0, 0), line, font=font_quote)
        line_w = line_bbox[2] - line_bbox[0]
        lx = (width - line_w) // 2
        ly = quote_start_y + i * line_height + 14
        draw.text((lx, ly), line, fill=BLACK, font=font_quote)

    # 右引号
    if quote_lines:
        last_y = quote_start_y + (len(quote_lines) - 1) * line_height + 14
        last_bbox = draw.textbbox((0, 0), quote_lines[-1], font=font_quote)
        last_end_x = (width + (last_bbox[2] - last_bbox[0])) // 2
        draw.text(
            (min(last_end_x + 4, width - margin - 34), last_y),
            "\u201d", fill=RED, font=font_quote_mark,
        )

    # ─── 底部装饰：小菱形 ───
    cx, cy = width // 2, height - banner_h - margin // 2 - 4
    d = 5
    draw.polygon([(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)], fill=RED)
    # 两侧小点
    draw.ellipse([(cx - 16, cy - 2), (cx - 12, cy + 2)], fill=RED)
    draw.ellipse([(cx + 12, cy - 2), (cx + 16, cy + 2)], fill=RED)

    # 保存图片
    img.save(output_path, "PNG")
    return {
        "output": output_path,
        "width": width,
        "height": height,
        "date": date_str,
        "weekday": weekday,
        "weather": weather_text,
        "quote": quote_text,
    }


# ============================================================
# 对外暴露的星期数据
# ============================================================

def get_weekday_zh(index: int) -> str:
    return _WEEKDAYS_ZH[index]


def get_weekday_en(index: int) -> str:
    return _WEEKDAYS_EN[index]
