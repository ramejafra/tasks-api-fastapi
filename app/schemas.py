"""
app/schemas.py
==============
Esquemas Pydantic de entrada/salida (API) separados de los modelos SQL.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import TaskPriority, TaskStatus

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class UserCreate(BaseModel):
    email: str
    password: Annotated[str, Field(min_length=8, max_length=128)]
    name: str = ""

    @field_validator("email")
    @classmethod
    def email_valido(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("email inválido")
        return v

    @field_validator("password")
    @classmethod
    def password_no_trivial(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("la contraseña debe incluir al menos un dígito")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    created_at: dt.datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ----------------------------- Tasks -----------------------------


class TaskCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: str = ""
    status: TaskStatus = TaskStatus.pending
    priority: TaskPriority = TaskPriority.medium
    due_date: dt.date | None = None


class TaskUpdate(BaseModel):
    """Todos los campos opcionales: PATCH parcial."""

    title: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: dt.date | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    due_date: dt.date | None
    created_at: dt.datetime
    updated_at: dt.datetime


class TaskList(BaseModel):
    """Respuesta paginada estándar."""

    items: list[TaskOut]
    total: int
    skip: int
    limit: int
