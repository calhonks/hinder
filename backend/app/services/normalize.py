from __future__ import annotations
from typing import List, Dict

ALIASES = {
    "llms": "llm",
    "react.js": "react",
    "pyTorch": "pytorch",
}


def _norm_one(s: str) -> str:
    key = s.strip().lower()
    return ALIASES.get(key, key)


def normalize_list(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in items or []:
        n = _norm_one(x)
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out
