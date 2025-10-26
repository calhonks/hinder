import json
from typing import List, Dict, Any

def list_to_json(lst: List[str] | None) -> str:
    return json.dumps(lst or [])


def json_to_list(s: str | None) -> List[str]:
    try:
        return list(json.loads(s or "[]"))
    except Exception:
        return []


def dict_to_json(d: Dict[str, Any] | None) -> str:
    try:
        return json.dumps(d or {})
    except Exception:
        return "{}"


def json_to_dict(s: str | None) -> Dict[str, Any]:
    try:
        v = json.loads(s or "{}")
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}
