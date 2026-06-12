"""Shared JSON parsing helpers used across routers and WebSocket handlers."""
import json
import re
from typing import Any, Optional, List, Dict


def parse_json_field(value: Any) -> Any:
    """Parse a JSON string field, return parsed object or None.

    Handles:
    - None -> None
    - Already parsed dict/list -> returned as-is
    - JSON string -> parsed object
    - Invalid JSON -> None
    """
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def parse_acknowledged_by(value: Any) -> List[int]:
    """Parse acknowledged_by JSON field, always returns a list.

    Handles:
    - None -> []
    - Already a list -> returned as-is
    - JSON string -> parsed list
    - Invalid JSON -> []
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def extract_json_array(text: str) -> Optional[List]:
    """Extract a JSON array from text (handles markdown code blocks etc)."""
    if not text:
        return None
    # Strip markdown code fences first
    cleaned = re.sub(r'```(?:json)?\s*', '', text).strip()
    # Use bracket depth tracking to find the outermost balanced array
    start = cleaned.find('[')
    if start == -1:
        # Fallback: try parsing entire text
        try:
            result = json.loads(cleaned)
            return result if isinstance(result, list) else None
        except json.JSONDecodeError:
            return None
    depth = 0
    for i in range(start, len(cleaned)):
        if cleaned[i] == '[':
            depth += 1
        elif cleaned[i] == ']':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start:i + 1])
                except json.JSONDecodeError:
                    return None
    # Fallback: try entire text
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def extract_json_object(text: str) -> Optional[Dict]:
    """Extract a JSON object from text (handles markdown code blocks etc)."""
    if not text:
        return None
    # Strip markdown code fences first
    cleaned = re.sub(r'```(?:json)?\s*', '', text).strip()
    start = cleaned.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(cleaned)):
        if cleaned[i] == '{':
            depth += 1
        elif cleaned[i] == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None
