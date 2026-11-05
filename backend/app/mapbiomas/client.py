"""Cliente async de la API GraphQL de MapBiomas Alerta.

Las credenciales y el token viven solo en el servidor (FR-017) y nunca se registran en logs.
"""

import asyncio
import logging
import time

import httpx

from app.config import settings
from app.mapbiomas.queries import SIGN_IN_MUTATION

log = logging.getLogger("app.mapbiomas")

_AUTH_HINTS = ("unauthorized", "unauthenticated", "not authorized", "invalid token", "token", "login")


class MapBiomasError(Exception):
    """La API respondió con un error (consulta inválida, recurso no encontrado...)."""


class MapBiomasUnavailable(Exception):
    """La API no respondió a tiempo o devolvió un error de servidor."""


class MapBiomasAuthError(MapBiomasError):
    pass


class MapBiomasClient:
    def __init__(self, url: str | None = None, email: str | None = None, password: str | None = None,
                 timeout: float | None = None):
        self.url = url or settings.mapbiomas_api_url
        self.email = email if email is not None else settings.mapbiomas_email
        self.password = password if password is not None else settings.mapbiomas_password
        self.timeout = timeout or settings.mapbiomas_timeout_s
        self._token: str | None = None
        self._login_lock = asyncio.Lock()

    async def _post(self, query: str, variables: dict, token: str | None) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        op = query.strip().split("(", 1)[0].split("{", 1)[0].strip()
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as http:
                resp = await http.post(self.url, json={"query": query, "variables": variables},
                                       headers=headers)
        except httpx.HTTPError as e:
            log.warning("mapbiomas op=%r error=%s dur=%.2fs", op, type(e).__name__,
                        time.perf_counter() - started)
            raise MapBiomasUnavailable(type(e).__name__) from e

        dur = time.perf_counter() - started
        if resp.status_code in (401, 403):
            log.info("mapbiomas op=%r status=%s dur=%.2fs", op, resp.status_code, dur)
            raise MapBiomasAuthError(f"HTTP {resp.status_code}")
        if resp.status_code >= 500:
            log.warning("mapbiomas op=%r status=%s dur=%.2fs", op, resp.status_code, dur)
            raise MapBiomasUnavailable(f"HTTP {resp.status_code}")
        try:
            body = resp.json()
        except ValueError as e:
            log.warning("mapbiomas op=%r invalid-json status=%s dur=%.2fs", op, resp.status_code, dur)
            raise MapBiomasUnavailable("Respuesta no JSON") from e

        errors = body.get("errors")
        if errors:
            msg = "; ".join(str(err.get("message", err)) for err in errors)
            log.info("mapbiomas op=%r graphql-error=%r dur=%.2fs", op, msg[:200], dur)
            if any(h in msg.lower() for h in _AUTH_HINTS):
                raise MapBiomasAuthError(msg)
            raise MapBiomasError(msg)
        log.info("mapbiomas op=%r ok dur=%.2fs", op, dur)
        return body.get("data") or {}

    async def _login(self) -> str:
        async with self._login_lock:
            if self._token:
                return self._token
            if not self.email or not self.password:
                raise MapBiomasAuthError("Faltan MAPBIOMAS_EMAIL / MAPBIOMAS_PASSWORD")
            data = await self._post(SIGN_IN_MUTATION, {"email": self.email, "password": self.password}, None)
            self._token = data["signIn"]["token"]
            return self._token

    async def execute(self, query: str, variables: dict | None = None) -> dict:
        """Ejecuta una query autenticada; ante error de autenticación, re-login una vez."""
        variables = variables or {}
        token = self._token or await self._login()
        try:
            return await self._post(query, variables, token)
        except MapBiomasAuthError:
            self._token = None
            token = await self._login()
            return await self._post(query, variables, token)


_client: MapBiomasClient | None = None


def get_mapbiomas_client() -> MapBiomasClient:
    """Dependencia FastAPI: instancia única (comparte el token en memoria)."""
    global _client
    if _client is None:
        _client = MapBiomasClient()
    return _client
