"""
app/routers/auth.py
===================
POST /auth/register  → 201 + Token
POST /auth/login     → 200 + Token
GET  /auth/me        → 200 UserOut (requiere token)
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from ..database import get_session
from ..models import User
from ..schemas import Token, UserCreate, UserOut
from ..security import create_access_token, decode_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=False)
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(credentials: CredentialsDep, session: SessionDep) -> User:
    """Dependency reutilizable por los demás routers."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "El usuario ya no existe")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, session: SessionDep) -> Token:
    email = payload.email.strip().lower()
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese email ya está registrado")

    user = User(
        email=email,
        name=payload.name.strip(),
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return Token(
        access_token=create_access_token(user.id or 0),
        expires_in=400,  # valor informativo para clientes
    )


@router.post("/login", response_model=Token)
def login(payload: UserCreate, session: SessionDep) -> Token:
    email = payload.email.strip().lower()
    user = session.exec(select(User).where(User.email == email)).first()

    not_ok = user is None or not verify_password(payload.password, user.hashed_password)
    if not_ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    assert user is not None

    return Token(access_token=create_access_token(user.id or 0), expires_in=400)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUserDep) -> User:
    return user
