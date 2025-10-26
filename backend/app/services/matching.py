from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from .embeddings import embed
from .chroma_store import query as chroma_query


def jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a or []), set(b or [])
    if not sa and not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def build_query_summary(user: Dict[str, Any], topic: Optional[str]) -> str:
    parts = [user.get("name") or "", user.get("headline") or ""]
    skills = ", ".join(user.get("skills_norm") or [])
    topics = ", ".join((user.get("topics") or []) + ([topic] if topic else []))
    parts += [skills, topics]
    return " | ".join([p for p in parts if p])


def retrieve_candidates(user_profile: Dict[str, Any], k: int = 20, topic: Optional[str] = None, exclude_id: Optional[str] = None, hackathon: Optional[str] = None):
    query_text = build_query_summary(user_profile, topic)
    qvec = embed(query_text)

    where = {"available_now": True}
    if hackathon:
        where["hackathon"] = hackathon

    # Chroma python client may not support 'where_not' – query first then filter
    res = chroma_query(qvec, n_results=max(50, k), where=where)

    # chroma returns dict with metadatas, ids, distances or similar. We'll use metadatas.
    ids = res.get("ids", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    embs_scores = res.get("distances", [[]])[0] if "distances" in res else None

    # filter excluded id if provided
    if exclude_id:
        filtered = [(i, m, d) for i, m, d in zip(ids, metas, embs_scores or [None]*len(ids)) if i != exclude_id]
        if filtered:
            ids, metas, embs_scores = zip(*filtered)
            ids, metas, embs_scores = list(ids), list(metas), list(embs_scores)
        else:
            ids, metas, embs_scores = [], [], []

    return ids, metas, embs_scores


def blend_scores(user: Dict[str, Any], metas: List[Dict[str, Any]], vector_scores: Optional[List[float]] = None) -> Tuple[List[float], List[float], List[float]]:
    sv = []
    sk = []
    sb = []
    u_skills = user.get("skills_norm") or []
    u_topics = user.get("topics") or []
    for i, m in enumerate(metas):
        kv = jaccard(u_skills + u_topics, (m.get("skills_norm") or []) + (m.get("topics") or []))
        sk.append(kv)
        vv = 1.0 - vector_scores[i] if vector_scores else 0.5  # if distances, invert to similarity
        sv.append(vv)
        sb.append(0.75 * vv + 0.25 * kv)
    return sv, sk, sb
