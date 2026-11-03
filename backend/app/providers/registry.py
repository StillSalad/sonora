"""Istanze condivise degli adapter. Nei test si sostituiscono con app.dependency_overrides."""
import threading
import time
from functools import lru_cache

import httpx

from ..config import get_settings
from .itunes import ItunesAdapter


@lru_cache
def _client() -> httpx.Client:
    return httpx.Client(headers={"User-Agent": "SONORA/0.2"})


@lru_cache
def _itunes() -> ItunesAdapter:
    return ItunesAdapter(_client(), get_settings().store_country)


def get_live_adapter():
    s = get_settings()
    return _itunes() if (s.itunes_enabled and s.live_search) else None


class QueryCache:
    """Evita di richiedere a iTunes la stessa ricerca più volte (24 ore)."""
    def __init__(self, ttl: float = 86400, max_items: int = 5000):
        self.ttl, self.max_items, self._d, self._lock = ttl, max_items, {}, threading.Lock()

    def fresh(self, key: str) -> bool:
        with self._lock:
            t = self._d.get(key)
            return t is not None and time.monotonic() - t < self.ttl

    def mark(self, key: str) -> None:
        with self._lock:
            if len(self._d) >= self.max_items:
                self._d.clear()
            self._d[key] = time.monotonic()


search_cache = QueryCache()
