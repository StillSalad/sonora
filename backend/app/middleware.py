"""Request id, header di sicurezza, protezione CSRF e rate limit."""
import time
import uuid
from collections import defaultdict, deque
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import get_settings

UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}


class RequestContext(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        response = await call_next(request)
        response.headers["x-request-id"] = request.state.request_id
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
        response.headers["permissions-policy"] = "camera=(), microphone=(), geolocation=()"
        if get_settings().is_production:
            response.headers["strict-transport-security"] = "max-age=31536000; includeSubDomains"
        return response


class CsrfGuard(BaseHTTPMiddleware):
    """Cookie SameSite=Lax + controllo Origin + header custom sulle richieste che modificano dati.
    Un sito terzo non può impostare X-Sonora-Client senza passare dal preflight CORS."""
    async def dispatch(self, request: Request, call_next):
        if request.method in UNSAFE and request.url.path.startswith("/api/"):
            origin = request.headers.get("origin")
            allowed = {_origin(get_settings().frontend_origin), _origin(str(request.base_url))}
            if origin and _origin(origin) not in allowed:
                return _err(request, 403, "csrf_origin", "Origine della richiesta non consentita.")
            if request.headers.get("x-sonora-client") != "web":
                return _err(request, 403, "csrf_header", "Richiesta non valida.")
        return await call_next(request)


class RateLimit(BaseHTTPMiddleware):
    """Limite in memoria per processo. In produzione con più istanze sostituire con Redis."""
    def __init__(self, app, rules: dict[str, tuple[int, int]]):
        super().__init__(app)
        self.rules = rules
        self.hits: dict[tuple[str, str], deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        rule = self.rules.get(request.url.path)
        if rule and request.method in UNSAFE:
            limit, window = rule
            key = (request.url.path, client_ip(request))
            now = time.monotonic()
            q = self.hits[key]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return _err(request, 429, "rate_limited", "Troppi tentativi. Riprova tra qualche minuto.")
            q.append(now)
        return await call_next(request)


def client_ip(request: Request) -> str:
    """Dietro Netlify e Render tutte le richieste arrivano dai loro server: l'IP del visitatore
    è il primo di X-Forwarded-For. Lo leggiamo solo se TRUST_PROXY=true."""
    if get_settings().trust_proxy:
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd.strip():
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "?"


def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _err(request: Request, status: int, code: str, message: str):
    rid = getattr(request.state, "request_id", uuid.uuid4().hex)
    return JSONResponse({"code": code, "message": message, "request_id": rid}, status_code=status)
