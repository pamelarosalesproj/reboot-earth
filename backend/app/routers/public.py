"""Consulta pública por CNPJ, sin sesión (feature 002, FR-101…107)."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.db import get_session
from app.mapbiomas.client import MapBiomasClient, get_mapbiomas_client
from app.rate_limit import public_search_limit
from app.schemas import PublicCnpjReport
from app.services.cnpj_report import build_public_report
from app.validators import normalize_cnpj

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/cnpj/{cnpj:path}", response_model=PublicCnpjReport,
            dependencies=[Depends(public_search_limit)])
async def public_cnpj(
    cnpj: str,
    db: Session = Depends(get_session),
    client: MapBiomasClient = Depends(get_mapbiomas_client),
):
    try:
        digits = normalize_cnpj(cnpj)
    except ValueError:
        return JSONResponse({"detail": "CNPJ inválido", "field": "cnpj", "invalid_values": []},
                            status_code=422)
    return await build_public_report(db, client, digits)
