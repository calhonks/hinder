from __future__ import annotations
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from ..config import CHROMA_DIR, CHROMA_COLLECTION
import os
import json

os.makedirs(CHROMA_DIR, exist_ok=True)
_client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
_collection = _client.get_or_create_collection(name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"})


def upsert(profile_id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
    # Chroma requires metadata values to be primitives. JSON-encode others.
    sanitized: Dict[str, Any] = {}
    for k, v in (metadata or {}).items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            sanitized[k] = v
        else:
            try:
                sanitized[k] = json.dumps(v)
            except Exception:
                sanitized[k] = str(v)
    _collection.upsert(ids=[profile_id], embeddings=[embedding], metadatas=[sanitized])


def delete(profile_id: str) -> None:
    _collection.delete(ids=[profile_id])


def query(query_embedding: List[float], n_results: int = 50, where: Optional[Dict[str, Any]] = None):
    return _collection.query(query_embeddings=[query_embedding], n_results=n_results, where=where)
