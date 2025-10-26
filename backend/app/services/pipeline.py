from __future__ import annotations
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select
from ..db.models import Profile, Upload
from ..db.session import get_session
from .pdf import extract_text
from .parsing import extract as parse_extract
from .normalize import normalize_list
from .embeddings import embed
from .chroma_store import upsert as chroma_upsert, delete as chroma_delete
from .sse import broker
from datetime import datetime, timezone
import traceback


def _json_list(s: Optional[str]) -> List[str]:
    import json
    try:
        return list(json.loads(s or "[]"))
    except Exception:
        return []


def _list_json(lst: Optional[List[str]]) -> str:
    import json
    return json.dumps(lst or [])


def _summary(profile: Profile) -> str:
    skills = ", ".join(_json_list(profile.skills_norm_json))
    topics = ", ".join(_json_list(profile.topics_json))
    return f"{profile.name or ''} | {profile.headline or ''} | {skills} | {topics}"


async def run(profile_id: str) -> None:
    db = get_session()
    try:
        prof = db.get(Profile, profile_id)
        if not prof:
            return
        try:
            print(f"[pipeline] start profile_id={profile_id}")
            prof.status = "parsing"
            db.add(prof)
            db.commit()
            await broker.publish(profile_id, {"status": "parsing"})

            raw_text_parts: List[str] = []

            # ingest PDF if present
            if prof.resume_file_id:
                import os as os_module
                up = db.get(Upload, prof.resume_file_id)
                if not up:
                    print(f"[pipeline] Upload record not found for file_id={prof.resume_file_id}")
                    # Check if file exists on disk anyway
                    from ..config import UPLOAD_DIR
                    potential_path = os_module.path.join(UPLOAD_DIR, f"{prof.resume_file_id}.pdf")
                    if os_module.path.exists(potential_path):
                        print(f"[pipeline] But file exists on disk at {potential_path}")
                elif not up.path:
                    print(f"[pipeline] Upload path is empty for file_id={prof.resume_file_id}")
                else:
                    try:
                        txt = extract_text(up.path)
                        if txt:
                            raw_text_parts.append(txt)
                        print(f"[pipeline] extracted PDF text bytes={len(txt or '')}")
                    except Exception:
                        print("[pipeline] PDF extract failed:\n" + traceback.format_exc())

            # ingest from linkedin url via brightdata later (stubbed)

            raw_text = "\n".join([p for p in raw_text_parts if p])
            print(f"[pipeline] total raw_text chars={len(raw_text)}")

            parsed = await parse_extract(raw_text)
            print(f"[pipeline] parsed keys={list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}")

            # update basic fields (best-effort)
            prof.name = prof.name or parsed.get("name")
            prof.headline = prof.headline or parsed.get("headline")
            tech = parsed.get("skills", {}).get("tech", [])
            domain = parsed.get("skills", {}).get("domain", [])
            skills_norm = normalize_list(list(set((_json_list(prof.skills_norm_json) + tech + domain))))
            
            # Merge parsed interests with existing topics (don't override user's selected topics)
            parsed_interests = parsed.get("interests", [])
            existing_topics = _json_list(prof.topics_json)
            merged_topics = list(set(existing_topics + parsed_interests))
            topics = normalize_list(merged_topics)
            
            print(f"[pipeline] skills_norm_count={len(skills_norm)} topics_count={len(topics)}")
            prof.skills_norm_json = _list_json(skills_norm)
            prof.topics_json = _list_json(topics)

            prof.status = "embedding"
            prof.updated_at = datetime.now(timezone.utc)
            db.add(prof)
            db.commit()
            await broker.publish(profile_id, {"status": "embedding"})

            # build summary and embed
            summary = _summary(prof)
            try:
                vec = embed(summary)
                print(f"[pipeline] embedding_dim={len(vec) if hasattr(vec, '__len__') else 'unknown'}")
            except Exception:
                print("[pipeline] embed failed:\n" + traceback.format_exc())
                raise

            metadata = {
                "id": prof.id,
                "name": prof.name,
                "headline": prof.headline,
                "skills_norm": skills_norm,
                "topics": topics,
                "school": prof.school,
                "company": prof.company,
                "seniority": prof.seniority,
                "available_now": prof.available_now,
                "hackathon": prof.hackathon,
            }
            print(metadata)
            try:
                chroma_upsert(profile_id, vec, metadata)
                print("[pipeline] chroma upsert ok")
            except Exception:
                print("[pipeline] chroma upsert failed:\n" + traceback.format_exc())
                raise

            prof.status = "ready"
            prof.updated_at = datetime.now(timezone.utc)
            db.add(prof)
            db.commit()
            await broker.publish(profile_id, {"status": "ready"})

        except Exception:
            print("[pipeline] ERROR:\n" + traceback.format_exc())
            prof = db.get(Profile, profile_id)
            if prof:
                prof.status = "error"
                db.add(prof)
                db.commit()
            await broker.publish(profile_id, {"status": "error"})
    finally:
        db.close()


def delete_profile_index(profile_id: str) -> None:
    try:
        chroma_delete(profile_id)
    except Exception:
        pass
