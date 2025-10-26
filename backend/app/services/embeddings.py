from __future__ import annotations
from typing import List
import hashlib
import numpy as np
import httpx
from ..config import EMBEDDINGS_PROVIDER, GEMINI_API_KEY

# Dev-friendly deterministic embedding without external calls.
# Hash n-grams into a fixed-size vector.

DIM = 768


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in text.strip().split() if t.strip()]


def _hash_token(tok: str) -> int:
    return int(hashlib.md5(tok.encode()).hexdigest(), 16)


def _embed_local(text: str) -> List[float]:
    vec = np.zeros(DIM, dtype=np.float32)
    toks = _tokenize(text)[:4000]
    for t in toks:
        h = _hash_token(t) % DIM
        vec[h] += 1.0
    # l2 normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def _embed_gemini(text: str) -> List[float]:
    # Uses Google Generative Language API text-embedding-004
    if not GEMINI_API_KEY:
        return _embed_local(text)
    url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
    params = {"key": GEMINI_API_KEY}
    payload = {"model": "text-embedding-004", "content": {"parts": [{"text": text[:8000]}]}}
    try:
        resp = httpx.post(url, params=params, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        vec = data.get("embedding", {}).get("values")
        if isinstance(vec, list) and vec:
            return vec
    except Exception:
        pass
    return _embed_local(text)


def embed(text: str) -> List[float]:
    provider = (EMBEDDINGS_PROVIDER or "local").lower()
    if provider == "gemini":
        return _embed_gemini(text)
    return _embed_local(text)
