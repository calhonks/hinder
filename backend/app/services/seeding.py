from __future__ import annotations
from typing import List
from datetime import datetime
import random
from sqlmodel import Session
from ..db.models import Profile
from ..utils.ids import new_id
from ..utils.json import list_to_json
from .embeddings import embed
from .chroma_store import upsert as chroma_upsert

TOPICS = [
    "Agentic AI","Drones","LLM Eval","RAG","Web3","Data Infra","AR/VR","Open Source","VC chat"
]
SKILLS = [
    "Python","TypeScript","React","ROS","Rust","Go","RAG","LLM","Prompting","SQL","Docker","Kubernetes","AR","VR","Solana","GraphQL","PyTorch","TensorFlow"
]
HACKATHONS = ["calhacks12.0","ethglobal-nyc","hackmit","treehacks","la-hacks"]


def _pick_many(src: List[str], n: int) -> List[str]:
    return random.sample(src, k=min(n, len(src)))


def generate_synthetic_profiles(db: Session, count: int = 12) -> int:
    added = 0
    for i in range(count):
        pid = new_id("p")
        topics = _pick_many(TOPICS, 3)
        skills = list(dict.fromkeys(_pick_many(SKILLS, 6)))
        available_now = random.random() > 0.4
        hackathon = random.choice(HACKATHONS)
        prof = Profile(
            id=pid,
            name=f"Seed {pid[-4:]}",
            headline=f"Excited about {topics[0]}",
            email=None,
            school=None,
            company=None,
            seniority=None,
            linkedin_url=None,
            resume_file_id=None,
            resume_file_name=None,
            skills_norm_json=list_to_json(skills),
            interests_json=list_to_json(topics),
            topics_json=list_to_json(topics),
            available_now=available_now,
            status="embedding",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            source=None,
            hackathon=hackathon,
        )
        db.add(prof)
        db.commit()
        # embed and index
        summary = f"{prof.name or ''} | {prof.headline or ''} | {', '.join(skills)} | {', '.join(topics)}"
        vec = embed(summary)
        metadata = {
            "id": prof.id,
            "name": prof.name,
            "headline": prof.headline,
            "skills_norm": skills,
            "topics": topics,
            "school": prof.school,
            "company": prof.company,
            "seniority": prof.seniority,
            "available_now": prof.available_now,
            "hackathon": prof.hackathon,
        }
        chroma_upsert(prof.id, vec, metadata)
        prof.status = "ready"
        prof.updated_at = datetime.utcnow()
        db.add(prof)
        db.commit()
        added += 1
    return added
