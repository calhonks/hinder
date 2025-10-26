from __future__ import annotations
from typing import Dict, Any, List, Optional
import json
import httpx
from pydantic import BaseModel, ValidationError
from ..config import ANTHROPIC_API_KEY, CLAUDE_MODEL
import traceback


class SkillsModel(BaseModel):
    tech: List[str] = []
    domain: List[str] = []


class RoleModel(BaseModel):
    title: Optional[str] = None
    org: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


class ParseOutput(BaseModel):
    name: Optional[str] = None
    headline: Optional[str] = None
    roles: List[RoleModel] = []
    skills: SkillsModel = SkillsModel()
    interests: List[str] = []
    education: List[str] = []  # Can be list of strings or dict; we'll flatten it
    links: List[str] = []  # Can be list of strings or dict; we'll flatten it
    
    @classmethod
    def model_validate(cls, obj):
        # Flatten education if it's a dict
        if isinstance(obj.get("education"), dict):
            edu = obj["education"]
            obj["education"] = [f"{edu.get('degree', '')} from {edu.get('institution', '')}".strip()]
        elif not isinstance(obj.get("education"), list):
            obj["education"] = []
        
        # Flatten links if it's a dict
        if isinstance(obj.get("links"), dict):
            links_dict = obj["links"]
            obj["links"] = [v for v in links_dict.values() if v]
        elif not isinstance(obj.get("links"), list):
            obj["links"] = []
        
        return super().model_validate(obj)


SYSTEM_PROMPT = (
    "You are a precise information extraction service. "
    "Extract concise fields from the provided resume/profile text. "
    "Return ONLY a strict JSON object with keys: name, headline, roles (title, org, start, end), "
    "skills { tech: [], domain: [] }, interests, education, links. "
    "Do not add any commentary. Keep arrays small and relevant."
)


def _default_output() -> Dict[str, Any]:
    return ParseOutput().model_dump()


def _chunk_text(t: str, max_len: int = 12000) -> str:
    # Keep the first max_len characters; simple truncation for latency.
    t = t or ""
    if len(t) <= max_len:
        return t
    return t[:max_len]


async def _call_anthropic(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        # No text to parse; return defaults
        return _default_output()
    if not ANTHROPIC_API_KEY:
        return _default_output()
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": text}]}
        ],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(url, headers=headers, json=payload)
            status = r.status_code
            # Try JSON first; if fails, log text
            try:
                data = r.json()
            except Exception:
                print("Anthropic non-JSON response status=", status)
                # print("Body:\n", r.text[:2000])
                r.raise_for_status()
                raise
            if status >= 400:
                # Error payloads are JSON; print them
                print("Anthropic error status=", status, "body=", data)
                r.raise_for_status()
        except Exception:
            print("Anthropic request failed:\n" + traceback.format_exc())
            return _default_output()
    # Anthropic messages API: response in content[0].text
    content = data.get("content", [])
    if not content:
        print("Anthropic response has no content")
        return _default_output()
    raw = content[0].get("text", "{}")
    print(f"Anthropic raw response (first 500 chars): {raw[:500]}")
    try:
        obj = json.loads(raw)
        parsed = ParseOutput.model_validate(obj)
        result = parsed.model_dump()
        print(f"Parsed result: {result}")
        return result
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Failed to parse Anthropic response: {e}")
        print(f"Raw response: {raw}")
        return _default_output()


async def extract(raw_text: str) -> Dict[str, Any]:
    text = _chunk_text(raw_text)
    if not text or not text.strip():
        # No text to parse; return defaults
        return _default_output()
    # Retry up to 2 times on HTTP errors
    for _ in range(2):
        try:
            return await _call_anthropic(text)
        except Exception:
            continue
    return _default_output()
