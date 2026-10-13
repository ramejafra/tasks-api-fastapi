"""
app/main.py
===========
Punto de entrada de la API.

Ejecutar en desarrollo:
    uvicorn app.main:app --reload --port 8000
Docs interactivas: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import create_tables
from .routers import auth, tasks

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas al arrancar (demo: sin migraciones formales)
    create_tables()
    yield


app = FastAPI(
    title="Tasks API (FastAPI)",
    description="API REST de tareas con JWT, filtrado y paginación. "
    "Proyecto de portafolio: arquitectura limpia y testeada.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok"}
