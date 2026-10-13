"""
app/security.py
===============
Hashing de contraseñas (passlib/bcrypt) y tokens JWT (PyJWT).
"""
from __future__ import annotations

import datetime as dt

import jwt

from .config import get_settings

settings = get_settings()

try:
    from passlib.context import CryptContext

    _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(plain: str) -> str:
        return _pwd.hash(plain)

    def verify_password(plain: str, hashed: str) -> bool:
        return _pwd.verify(plain, hashed)

except Exception:  # pragma: no cover - fallback sin passlib/bcrypt
    import hashlib
    import secrets

    def hash_password(plain: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100_000)
        return f"pbkdf2${salt}${digest.hex()}"

    def verify_password(plain: str, hashed: str) -> bool:
        try:
            algo, salt, hex_digest = hashed.split("$")
        except ValueError:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100_000)
        return digest.hex() == hex_digest


def create_access_token(user_id: int) -> str:
    """JWT HS256 con `sub`, `iat` y `exp`."""
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(minutes=settings.jwt_expires_min)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> int | None:
    """Devuelve el user_id o None si el token es inválido/expirado."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.InvalidTokenError:
        return None
    sub = payload.get("sub")
    return int(sub) if sub and sub.isdigit() else None
