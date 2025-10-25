from sqlmodel import SQLModel, create_engine, Session
import os
from ..config import SQLITE_PATH

os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{SQLITE_PATH}", echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
