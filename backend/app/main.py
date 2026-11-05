import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import create_db_and_tables
from app.mapbiomas.client import MapBiomasError, MapBiomasUnavailable
from app.routers import auth, cars, dashboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="RebootEarth – Panel del productor", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(MapBiomasUnavailable)
async def mapbiomas_unavailable(_: Request, exc: MapBiomasUnavailable):
    return JSONResponse({"detail": "MapBiomas Alerta indisponível. Tente novamente mais tarde."},
                        status_code=503)


@app.exception_handler(MapBiomasError)
async def mapbiomas_error(_: Request, exc: MapBiomasError):
    log.warning("MapBiomas error: %s", str(exc)[:200])
    return JSONResponse({"detail": "Erro ao consultar o MapBiomas Alerta. Tente novamente mais tarde."},
                        status_code=503)


@app.exception_handler(RequestValidationError)
async def request_validation(_: Request, exc: RequestValidationError):
    """Formato del contrato: {detail, field, invalid_values}."""
    err = exc.errors()[0] if exc.errors() else {}
    loc = [str(p) for p in err.get("loc", []) if p not in ("body", "query", "path")]
    field = loc[0] if loc else None
    messages = {"email": "Email inválido", "password": "A senha deve ter pelo menos 8 caracteres"}
    detail = messages.get(field or "", err.get("msg", "Dados inválidos"))
    return JSONResponse({"detail": detail, "field": field, "invalid_values": []}, status_code=422)


app.include_router(auth.router, prefix="/api")
app.include_router(cars.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
