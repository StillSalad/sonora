import threading
import time


class Throttle:
    """Intervallo minimo tra due richieste allo stesso provider (thread-safe, per processo).
    iTunes Search API: ~20 richieste/minuto. MusicBrainz: 1 richiesta/secondo."""

    def __init__(self, min_interval: float, sleep=time.sleep, clock=time.monotonic):
        self.min_interval, self._sleep, self._clock = min_interval, sleep, clock
        self._last = -1e9
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            delta = self._clock() - self._last
            if delta < self.min_interval:
                self._sleep(self.min_interval - delta)
            self._last = self._clock()
