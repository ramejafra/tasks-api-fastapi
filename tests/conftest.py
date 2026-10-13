"""
tests/conftest.py
=================
Fixtures: base de datos SQLite en tmp y TestClient con tablas creadas.
Cada test arranca limpio (base nueva).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./_test_tasks.db"

from sqlmodel import SQLModel, create_engine  # noqa: E402

from app.database import get_session  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402


@pytest.fixture(scope="session")
def _db_file(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    path = Path(tmp_path_factory.mktemp("db")) / "tasks_test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///./{path.as_posix()}"
    yield path
    if path.exists():
        path.unlink()


@pytest.fixture()
def client(_db_file: Path) -> Iterator[TestClient]:
    """Nueva base + motor por test (aislamiento total)."""
    engine = create_engine(
        os.environ["DATABASE_URL"],
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    def override_session():
        from sqlmodel import Session

        with Session(engine) as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = override_session
    with TestClient(fastapi_app) as tc:
        yield tc
    fastapi_app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


def register_login(client: TestClient, email: str = "ana@x.com", password: str = "secreto123") -> str:
    """Helper: registra un usuario y devuelve el token JWT."""
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password, "name": "Ana"})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
