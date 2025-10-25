import json
from typing import List

def list_to_json(lst: List[str] | None) -> str:
    return json.dumps(lst or [])


def json_to_list(s: str | None) -> List[str]:
    try:
        return list(json.loads(s or "[]"))
    except Exception:
        return []
