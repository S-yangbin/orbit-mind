"""AI service layer using bailian-cli (bl) for dish recognition and meal planning."""
import json
import logging
import re
import subprocess
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)


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


def _extract_json_array(text: str) -> Optional[List]:
    """Extract a JSON array from text (handles markdown code blocks etc)."""
    if not text:
        return None
    # Try to find JSON array
    match = re.search(r'\[[\s\S]*?\]', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # Try parsing entire text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _extract_json_object(text: str) -> Optional[Dict]:
    """Extract a JSON object from text."""
    if not text:
        return None
    # Try to find JSON object
    # Use a more robust approach - find the outermost braces
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
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

    dishes = _extract_json_array(text)
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
    - Saturday & Sunday DINNER: child-friendly meals only

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
    child_prefs = ""
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

        if m["role"] == "child":
            child_prefs = f"喜欢 [{likes}]，不喜欢 [{dislikes}]"
            if note:
                child_prefs += f"，{note}"

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

    prompt = f"""你是一个家庭营养顾问。请为以下家庭制定未来一个月的周末菜单。

## 需要规划的日期
{dates_display}

## 家庭成员
{family_info}

## 过敏/忌口
{allergies_info}

## 孩子(6岁)的口味偏好
{child_prefs}

## 最近吃过的菜（尽量避免重复）
{recent_info}

## 要求

### 午餐（全家人吃，4人份）
- 每顿 4 菜 1 汤，荤素搭配，丰富一些
- 考虑全家人口味，荤素搭配合理
- 至少1道绿叶蔬菜
- 菜品以家常菜为主

### 晚餐（只给孩子吃，1人份）
- 每顿 1 菜 1 汤 或 1 菜 1 主食，分量适合6岁孩子
- 必须清淡、少油少盐、不辣
- 营养均衡，有蛋白质和蔬菜
- 做法简单，适合单独给孩子做
- 例如：番茄鸡蛋面、虾仁蒸蛋+米饭、肉末豆腐+青菜汤等

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
        ],
        "dinner": [
          {{"name":"虾仁蒸蛋","category":"荤菜","recipe":"鸡蛋打散加温水虾仁上锅蒸10分钟淋生抽"}},
          {{"name":"米饭","category":"主食","recipe":"大米洗净加水蒸熟"}}
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

    plan = _extract_json_object(text)
    if plan is None or "days" not in plan:
        logger.error("Failed to parse monthly weekend plan output: %s", text[:300])
        return None

    return plan
