"""Límite de consultas públicas por IP (FR-106, research R6).

Ventana deslizante en memoria. LIMITACIÓN: solo válido con un único proceso; con varios
workers o réplicas cada uno cuenta por separado y habría que mover el contador a un
almacén compartido (plan.md, Riesgos).
"""

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request

from app.config import settings


class SlidingWindowLimiter:
    def __init__(self, window_s: int = 3600, clock: Callable[[], float] = time.monotonic):
        self.window_s = window_s
        self.clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int) -> int | None:
        """Registra una consulta. None si se permite; si no, segundos hasta poder volver.
        Las consultas rechazadas no cuentan (no alargan la espera)."""
        now = self.clock()
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= now - self.window_s:
                hits.popleft()
            if len(hits) >= limit:
                return max(1, int(hits[0] + self.window_s - now + 0.999))
            hits.append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


class RateLimited(Exception):
    def __init__(self, retry_after_s: int):
        self.retry_after_s = retry_after_s


public_limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    if settings.trust_proxy_headers and (fwd := request.headers.get("x-forwarded-for")):
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def public_search_limit(request: Request) -> None:
    """Dependencia FastAPI: lanza RateLimited (→ 429 en main.py) al superar el límite."""
    retry = public_limiter.hit(client_ip(request), settings.public_search_limit_per_hour)
    if retry is not None:
        raise RateLimited(retry)
