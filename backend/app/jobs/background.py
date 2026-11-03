"""Import del catalogo in un thread del server web (piano gratuito: niente worker separati)."""
import logging
import threading
from datetime import datetime, timezone

import httpx
from sqlalchemy import func, select

from ..catalog.genres import DISCOVERY_TERMS
from ..config import get_settings
from ..db import SessionLocal
from ..models import Provider, ProviderTrack
from ..providers.itunes import ItunesAdapter
from .ingest import run

log = logging.getLogger("sonora.ingest")
_lock = threading.Lock()
status: dict = {"running": False, "started_at": None, "finished_at": None, "result": None, "error": None}


def start(chart_only: bool = False) -> bool:
    """Avvia l'import se non è già in corso. Restituisce False se ce n'è già uno."""
    if not _lock.acquire(blocking=False):
        return False
    status.update(running=True, started_at=datetime.now(timezone.utc).isoformat(), finished_at=None, result=None, error=None)

    def work():
        try:
            s = get_settings()
            with httpx.Client(headers={"User-Agent": "SONORA/0.3"}) as client:
                status["result"] = run(ItunesAdapter(client, s.store_country), list(DISCOVERY_TERMS), 40, chart_only)
        except Exception as e:  # noqa: BLE001 - lo stato deve sempre chiudersi
            log.exception("import fallito")
            status["error"] = str(e)
        finally:
            status.update(running=False, finished_at=datetime.now(timezone.utc).isoformat())
            _lock.release()

    threading.Thread(target=work, name="sonora-ingest", daemon=True).start()
    return True


def catalog_is_empty() -> bool:
    with SessionLocal() as db:
        n = db.scalar(select(func.count(ProviderTrack.id)).join(Provider, Provider.id == ProviderTrack.provider_id)
                      .where(Provider.name == "itunes"))
        return not n
