"""
app/config.py
=============
Configuración central. Las variables se leen del entorno (o de un `.env`)
para seguir buenas prácticas 12-factor.

Variables soportadas
--------------------
- DATABASE_URL   (default sqlite:///./tasks.db)
- JWT_SECRET     (en producción: obligatoria y aleatoria)
- JWT_EXPIRES_MIN  (default 30)
- CORS_ORIGINS   (default ["*"])
"""
from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Valores tipados de configuración de la aplicación."""

    def __init__(self) -> None:
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
        jwt_secret_env = os.getenv("JWT_SECRET", "")
        self.is_production: bool = os.getenv("ENV", "dev") == "production"

        if self.is_production and not jwt_secret_env:
            raise RuntimeError(
                "JWT_SECRET es obligatoria en producción. "
                "Genera una con: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        # En desarrollo, si no hay secreto se genera uno desechable
        self.jwt_secret: str = jwt_secret_env or secrets.token_urlsafe(48)

        self.jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expires_min: int = int(os.getenv("JWT_EXPIRES_MIN", "30"))
        self.cors_origins: list[str] = [
            o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
        ]

    @property
    def sqlite_kwargs(self) -> dict:
        """connect_args solo para SQLite (check_same_thread)."""
        if self.database_url.startswith("sqlite"):
            return {"connect_args": {"check_same_thread": False}}
        return {}


@lru_cache
def get_settings() -> Settings:
    """Settings como singleton (cacheado)."""
    return Settings()


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent
