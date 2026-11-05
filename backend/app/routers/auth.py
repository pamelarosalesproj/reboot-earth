from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.auth import (
    clear_session_cookie,
    create_session,
    current_producer,
    hash_password,
    set_session_cookie,
    verify_password,
)
from app.db import get_session
from app.models import AuthSession, Producer
from app.schemas import LoginRequest, Me, ProducerCarOut, RegisterRequest, ValidationErrorOut
from app.validators import normalize_cnpj

router = APIRouter(prefix="/auth", tags=["auth"])


def to_me(producer: Producer) -> Me:
    cars = sorted(producer.cars, key=lambda c: c.added_at)
    return Me(email=producer.email, cnpj=producer.cnpj,
              cars=[ProducerCarOut.model_validate(c, from_attributes=True) for c in cars])


def validation_error(detail: str, field: str, invalid: list[str] | None = None) -> JSONResponse:
    body = ValidationErrorOut(detail=detail, field=field, invalid_values=invalid or [])
    return JSONResponse(body.model_dump(), status_code=422)


@router.post("/register", status_code=201, response_model=Me)
def register(req: RegisterRequest, response: Response, db: Session = Depends(get_session)):
    """Cuenta con email, contraseña y CNPJ. Los CARs se añaden después desde el panel."""
    email = req.email.lower()
    if db.exec(select(Producer).where(Producer.email == email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Este email já está cadastrado. Faça login.")
    try:
        cnpj = normalize_cnpj(req.cnpj)
    except ValueError as e:
        return validation_error(str(e), "cnpj", [req.cnpj])

    producer = Producer(email=email, password_hash=hash_password(req.password), cnpj=cnpj)
    db.add(producer)
    db.commit()
    db.refresh(producer)

    set_session_cookie(response, create_session(db, producer))
    return to_me(producer)


@router.post("/login", response_model=Me)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_session)):
    producer = db.exec(select(Producer).where(Producer.email == req.email.strip().lower())).first()
    if not producer or not verify_password(req.password, producer.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou senha inválidos")
    set_session_cookie(response, create_session(db, producer))
    return to_me(producer)


@router.post("/logout", status_code=204)
def logout(producer: Producer = Depends(current_producer), db: Session = Depends(get_session)):
    for s in db.exec(select(AuthSession).where(AuthSession.producer_id == producer.id)).all():
        db.delete(s)
    db.commit()
    resp = Response(status_code=204)
    clear_session_cookie(resp)
    return resp


@router.get("/me", response_model=Me)
def me(producer: Producer = Depends(current_producer)):
    return to_me(producer)
