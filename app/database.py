"""
app/database.py
===============
Motor SQLAlchemy/SQLModel + sesión FastAPI.
"""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, **settings.sqlite_kwargs)


def create_tables() -> None:
    """Crea las tablas si no existen (sin migraciones: demo/portafolio)."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Depends(get_session)
