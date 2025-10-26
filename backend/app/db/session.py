from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
import os
from ..config import SQLITE_PATH

os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{SQLITE_PATH}", echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    # Add contact_info_json column if missing (for existing databases)
    try:
        with engine.connect() as conn:
            res = conn.execute(text("PRAGMA table_info('profile')"))
            cols = {row[1] for row in res}
            if 'contact_info_json' not in cols:
                conn.execute(text("ALTER TABLE profile ADD COLUMN contact_info_json TEXT DEFAULT '{}'"))
                conn.commit()
    except Exception:
        pass


def get_session() -> Session:
    return Session(engine)
