from typing import Iterator
from fastapi import Depends
from sqlmodel import Session
from .db.session import get_session

def get_db() -> Iterator[Session]:
    db = get_session()
    try:
        yield db
    finally:
        db.close()
