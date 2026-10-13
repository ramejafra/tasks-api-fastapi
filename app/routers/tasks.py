"""
app/routers/tasks.py
====================
CRUD de tareas con aislamiento por usuario:

POST   /tasks            → 201 TaskOut
GET    /tasks            → 200 TaskList (filtros: status, priority, q; paginación)
GET    /tasks/{id}       → 200 TaskOut | 404
PATCH  /tasks/{id}       → 200 TaskOut | 404
DELETE /tasks/{id}       → 204 | 404
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlmodel import Session, select

from ..database import get_session
from ..models import Task, TaskPriority, TaskStatus, User
from ..schemas import TaskCreate, TaskList, TaskOut, TaskUpdate
from .auth import CurrentUserDep, SessionDep

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task(task_id: int, user: User, session: Session) -> Task:
    """404 si no existe o no le pertenece (no filtrar info de existencia)."""
    task = session.get(Task, task_id)
    if task is None or task.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada")
    return task


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, user: CurrentUserDep, session: SessionDep) -> Task:
    task = Task(
        title=payload.title.strip(),
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        owner_id=user.id or 0,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.get("", response_model=TaskList)
def list_tasks(
    user: CurrentUserDep,
    session: SessionDep,
    status_filter: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: TaskPriority | None = None,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TaskList:
    statement_filter = Task.owner_id == user.id  # type: ignore[assignment]
    if status_filter is not None:
        statement_filter &= Task.status == status_filter  # type: ignore[assignment]
    if priority is not None:
        statement_filter &= Task.priority == priority  # type: ignore[assignment]
    if q:
        statement_filter &= (Task.title.contains(q)) | (Task.description.contains(q))  # type: ignore[assignment]

    query = select(Task).where(statement_filter)
    items = session.exec(query.offset(skip).limit(limit)).all()
    total = len(session.exec(query).all())

    return TaskList(items=list(items), total=total, skip=skip, limit=limit)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, user: CurrentUserDep, session: SessionDep) -> Task:
    return _get_owned_task(task_id, user, session)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    user: CurrentUserDep,
    session: SessionDep,
) -> Task:
    task = _get_owned_task(task_id, user, session)
    import datetime as dt

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(task, field, value)
    task.updated_at = dt.datetime.now(dt.timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, user: CurrentUserDep, session: SessionDep) -> Response:
    task = _get_owned_task(task_id, user, session)
    session.delete(task)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
