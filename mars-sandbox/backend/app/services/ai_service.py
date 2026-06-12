"""AI service layer using bailian-cli (bl) for dish recognition and meal planning."""
import json
import logging
import os
import subprocess
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from ..config import settings
from ..utils.json_helpers import extract_json_array, extract_json_object

logger = logging.getLogger(__name__)

# AI 壁纸生成主题模板（随季节自动选择）
_WALLPAPER_THEMES = [
    "春季繁花盛开的山谷，粉白色樱花与嫩绿新芽交相辉映，远处青山如黛，淡金色晨光透过花枝洒落，宁静温暖的田园风光",
    "夏日清晨的高山草原，翠绿草甸延伸至天际，野花点缀其间，蓝天白云倒映在清澈湖水中，清新明亮",
    "金秋时层林尽染的山谷，红枫金黄银杏色彩绚烂，清澈溪流穿越其中，夕阳余晖为远山镶上金边，丰饶宁静",
    "冬日雪后初晴的山景，银装素裹的松林覆盖山坡，天空湛蓝如洗，一缕暖阳穿过云层照亮雪地，纯洁静谧",
    "壮丽的星空夜景，璀璨银河横跨天际，前景是剪影般的远山与平静湖面，星光倒映水中，神秘浪漫",
    "海边日落全景，橙红色天空渐变为紫色，金色太阳缓缓沉入海平线，波光粼粼的海面映满霞光，温暖壮观",
    "清晨云海中的山峰，金色朝阳从云端升起，云海翻涌如棉絮，远山若隐若现，壮丽空灵",
    "竹林小径与中式庭院，翠绿竹林形成天然拱门，石板路蜿蜒其中，光影斑驳，禅意盎然",
]


def _run_bl(args: List[str], timeout: int = 120) -> Optional[str]:
    """Run a bl command and return stdout text, or None on failure."""
    cmd = [settings.BL_PATH] + args
    logger.info("Running bl command: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            logger.error("bl command failed (rc=%d): stderr=%s", result.returncode, result.stderr)
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logger.error("bl command timed out after %ds", timeout)
        return None
    except Exception as e:
        logger.error("bl command error: %s", e)
        return None


def recognize_dishes(image_path: str) -> List[Dict[str, Any]]:
    """Recognize dishes from a photo using bl omni vision model.

    Returns a list of dicts with keys: name, category
    """
    prompt = (
        "请仔细观察这张餐桌照片，识别出所有菜品。"
        "返回严格的 JSON 数组格式，每个元素包含 name(菜名) 和 category(分类:荤菜/素菜/汤/主食/凉菜/早点)。"
        "只返回 JSON，不要其他文字。"
        '示例格式: [{"name":"红烧肉","category":"荤菜"},{"name":"清炒西兰花","category":"素菜"}]'
    )
    output = _run_bl([
        "omni",
        "--image", image_path,
        "--message", prompt,
        "--text-only",
        "--output", "json",
    ], timeout=120)

    if not output:
        logger.warning("Dish recognition returned no output")
        return []

    logger.info("Dish recognition raw output: %s", output[:500])

    # Extract text from JSON API response
    text = output
    try:
        resp = json.loads(output)
        if isinstance(resp, dict):
            choices = resp.get("choices", [])
            if choices and "message" in choices[0]:
                text = choices[0]["message"].get("content", output)
            elif "output" in resp and "text" in resp["output"]:
                text = resp["output"]["text"]
            elif "content" in resp:
                text = resp["content"]
    except (json.JSONDecodeError, TypeError, IndexError, KeyError):
        pass

    logger.info("Dish recognition extracted text: %s", text[:500])

    dishes = extract_json_array(text)
    if dishes is None:
        logger.warning("Failed to parse dish recognition output: %s", output[:500])
        return []

    # Normalize results
    result = []
    for d in dishes:
        if isinstance(d, dict) and "name" in d:
            result.append({
                "name": d["name"].strip(),
                "category": d.get("category", "荤菜").strip(),
            })
    logger.info("Dish recognition result: %s", result)
    return result


def generate_monthly_weekend_plan(
    members: List[Dict[str, Any]],
    recent_dishes: List[str],
    start_date: date,
) -> Optional[Dict[str, Any]]:
    """Generate a monthly weekend meal plan using bl text chat.

    Only generates:
    - Saturday & Sunday LUNCH: full family meals (rich, 4-5 dishes + soup)

    Args:
        members: List of family member dicts
        recent_dishes: List of dish names from recent history
        start_date: Start date (will find next 4 weekends)

    Returns:
        Parsed JSON dict with "days" key, or None on failure
    """
    # Collect weekend dates for next 4 weeks
    weekend_dates = []
    current = start_date
    for _ in range(28):  # scan ~4 weeks
        if current.weekday() in (5, 6):  # Saturday=5, Sunday=6
            weekend_dates.append(current)
        current += timedelta(days=1)

    if not weekend_dates:
        return None

    # Build family info
    family_lines = []
    allergies_all = []
    for m in members:
        prefs = m.get("preferences") or {}
        likes = ", ".join(prefs.get("likes", [])) or "无特别偏好"
        dislikes = ", ".join(prefs.get("dislikes", [])) or "无"
        note = prefs.get("note", "")
        role_desc = {
            "father": "爸爸(中年)",
            "mother": "妈妈(中年)",
            "child": "孩子(6岁)",
            "grandma": "奶奶(59岁)",
        }.get(m["role"], m["name"])
        line = f"- {role_desc}：喜欢 [{likes}]，不喜欢 [{dislikes}]"
        if note:
            line += f"，备注: {note}"
        family_lines.append(line)

        allergies = m.get("allergies") or []
        if allergies:
            allergies_all.append(f"{m['name']}: {', '.join(allergies)}")

    family_info = "\n".join(family_lines)
    allergies_info = "\n".join(allergies_all) if allergies_all else "无"
    recent_info = ", ".join(recent_dishes[-50:]) if recent_dishes else "无历史记录"

    # Format weekend dates for display
    dates_display = "\n".join(
        f"  {d.strftime('%Y-%m-%d')} ({'周六' if d.weekday() == 5 else '周日'})"
        for d in weekend_dates
    )

    prompt = f"""你是一个家庭营养顾问。请为以下家庭制定未来一个月的周末午餐菜单。

## 需要规划的日期
{dates_display}

## 家庭成员
{family_info}

## 过敏/忌口
{allergies_info}

## 最近吃过的菜（尽量避免重复）
{recent_info}

## 要求

### 午餐（全家人吃，4人份）
- 每顿 4 菜 1 汤，荤素搭配，丰富一些
- 考虑全家人口味，荤素搭配合理
- 至少1道绿叶蔬菜
- 菜品以家常菜为主

### 通用要求
- 同一道菜在整个月内最多出现1次
- 菜品以家常菜为主，适合家庭烹饪
- 输出格式中每道菜都要给出简要食材和做法（2-3句话）

## 输出格式
返回严格 JSON，结构如下，不要其他文字：
{{
  "days": [
    {{
      "date": "{weekend_dates[0]}",
      "meals": {{
        "lunch": [
          {{"name":"红烧排骨","category":"荤菜","recipe":"排骨焯水后加酱油冰糖八角小火炖40分钟"}},
          {{"name":"清炒西兰花","category":"素菜","recipe":"西兰花焯水后蒜末爆炒加盐调味"}},
          {{"name":"番茄炒蛋","category":"素菜","recipe":"鸡蛋炒散番茄切块炒出汁加盐糖"}},
          {{"name":"凉拌黄瓜","category":"凉菜","recipe":"黄瓜拍碎加蒜末醋生抽辣椒油拌匀"}},
          {{"name":"紫菜蛋花汤","category":"汤","recipe":"紫菜撕碎水开后打入蛋花加盐调味"}}
        ]
      }}
    }}
  ]
}}"""

    output = _run_bl([
        "text", "chat",
        "--model", "qwen-plus",
        "--message", prompt,
        "--max-tokens", "4096",
        "--temperature", "0.8",
        "--output", "json",
    ], timeout=180)

    if not output:
        logger.error("Monthly weekend plan generation returned no output")
        return None

    # With --output json, extract text from API response structure
    text = output
    try:
        resp = json.loads(output)
        if isinstance(resp, dict):
            choices = resp.get("choices", [])
            if choices and "message" in choices[0]:
                text = choices[0]["message"].get("content", output)
            elif "output" in resp and "text" in resp["output"]:
                text = resp["output"]["text"]
    except (json.JSONDecodeError, TypeError, IndexError, KeyError):
        pass

    plan = extract_json_object(text)
    if plan is None or "days" not in plan:
        logger.error("Failed to parse monthly weekend plan output: %s", text[:300])
        return None

    return plan


def generate_wallpaper(prompt: Optional[str] = None) -> Optional[str]:
    """Generate a wallpaper image using bl image generate.

    Args:
        prompt: Custom prompt. If None, selects a seasonal theme automatically.

    Returns:
        The filename (not full path) of the saved wallpaper, or None on failure.
    """
    import random

    wallpaper_dir = settings.WALLPAPER_DIR
    os.makedirs(wallpaper_dir, exist_ok=True)

    if not prompt:
        # 根据当前月份选择季节主题
        month = date.today().month
        if month in (3, 4, 5):
            theme_idx = 0  # 春
        elif month in (6, 7, 8):
            theme_idx = random.choice([1, 6])  # 夏/云海
        elif month in (9, 10, 11):
            theme_idx = 2  # 秋
        else:
            theme_idx = random.choice([3, 4])  # 冬/星空
        # 30% 概率使用随机主题增加多样性
        if random.random() < 0.3:
            theme_idx = random.randint(0, len(_WALLPAPER_THEMES) - 1)
        prompt = _WALLPAPER_THEMES[theme_idx]

    full_prompt = f"高清风景壁纸，{prompt}，专业摄影，超高清画质，色彩丰富，构图优美"
    logger.info("AI 壁纸生成 prompt: %s", full_prompt)

    output = _run_bl([
        "image", "generate",
        "--prompt", full_prompt,
        "--size", "1920*1080",
        "--out-dir", wallpaper_dir,
        "--out-prefix", "ai-wallpaper",
        "--output", "json",
    ], timeout=120)

    if not output:
        logger.error("AI 壁纸生成返回空")
        return None

    try:
        result = json.loads(output)
        saved_files = result.get("saved", [])
        if saved_files:
            # 返回文件名（不含路径）
            filename = os.path.basename(saved_files[0])
            logger.info("AI 壁纸已生成: %s", filename)
            return filename
    except (json.JSONDecodeError, TypeError, IndexError) as e:
        logger.error("AI 壁纸生成输出解析失败: %s, output: %s", e, output[:500])

    return None
