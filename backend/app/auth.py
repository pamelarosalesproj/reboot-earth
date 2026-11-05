"""Contraseñas (Argon2) y sesión por cookie HttpOnly (research.md R3)."""

import secrets
from datetime import timedelta

from fastapi import Cookie, Depends, HTTPException, Response, status
from pwdlib import PasswordHash
from sqlmodel import Session

from app.config import settings
from app.db import as_utc, get_session, utcnow
from app.models import AuthSession, Producer

COOKIE_NAME = "session"
_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def create_session(db: Session, producer: Producer) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token=token, producer_id=producer.id,
                       expires_at=utcnow() + timedelta(days=settings.session_days)))
    db.commit()
    return token


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME, token,
        max_age=settings.session_days * 24 * 3600,
        httponly=True, samesite="lax", secure=settings.cookie_secure, path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def current_producer(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_session),
) -> Producer:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada")
    if not session:
        raise unauthorized
    auth = db.get(AuthSession, session)
    if not auth or as_utc(auth.expires_at) < utcnow():
        if auth:
            db.delete(auth)
            db.commit()
        raise unauthorized
    producer = db.get(Producer, auth.producer_id)
    if not producer:
        raise unauthorized
    return producer
