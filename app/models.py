"""
app/models.py
=============
Modelos SQLModel (SQLite por defecto, compatible con PostgreSQL).
"""
from __future__ import annotations

import datetime as dt
from enum import Enum

from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    name: str = ""
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: str = ""
    status: TaskStatus = Field(default=TaskStatus.pending, index=True)
    priority: TaskPriority = Field(default=TaskPriority.medium, index=True)
    due_date: dt.date | None = None
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc), index=True
    )
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )
    # Aislamiento de datos: toda tarea pertenece a un usuario
    owner_id: int = Field(foreign_key="users.id", index=True)
