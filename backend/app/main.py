from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, errors
from .config import get_settings
from .middleware import CsrfGuard, RateLimit, RequestContext
from .jobs import background
from .routers import auth, catalog, feed, internal, personal, system

API = "/api/v1"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    s = get_settings()
    # all'avvio: se il catalogo è vuoto o le classifiche hanno più di 20 ore, lo aggiorna da solo
    # in un thread (il server risponde subito). Sul piano gratuito il server riparte spesso: così il
    # catalogo resta fresco anche senza l'automazione giornaliera di GitHub.
    if s.ingest_on_start and s.itunes_enabled and (background.catalog_is_empty() or background.catalog_is_stale()):
        background.start(chart_only=False)
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="SONORA API", version=__version__, docs_url=f"{API}/docs", openapi_url=f"{API}/openapi.json",
                  lifespan=lifespan)
    errors.install(app)
    app.add_middleware(RateLimit, rules={f"{API}/auth/login": (10, 300), f"{API}/auth/register": (5, 3600), f"{API}/feed/events": (240, 60),
                                    f"{API}/feed/feedback": (60, 60)})
    app.add_middleware(CsrfGuard)
    app.add_middleware(CORSMiddleware, allow_origins=[s.frontend_origin], allow_credentials=True,
                       allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["content-type", "x-sonora-client", "x-sonora-device", "x-request-id"])
    app.add_middleware(RequestContext)
    app.include_router(system.router, prefix=API)
    app.include_router(auth.router, prefix=API)
    app.include_router(catalog.router, prefix=API)
    app.include_router(feed.router, prefix=API)
    app.include_router(internal.router, prefix=API)
    app.include_router(personal.router, prefix=API)
    return app


app = create_app()
