"""Adapter MusicBrainz: solo metadati (ISRC), mai audio.
Regole: User-Agent che identifica l'app con un contatto, massimo 1 richiesta al secondo.
https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting
"""
import httpx

from .base import ProviderUnavailable
from .throttle import Throttle

BASE = "https://musicbrainz.org/ws/2"


class MusicBrainzAdapter:
    name = "musicbrainz"

    def __init__(self, client: httpx.Client, contact: str, throttle: Throttle | None = None):
        if not contact:
            raise ValueError("MUSICBRAINZ_CONTACT è obbligatorio (email o URL per lo User-Agent)")
        self.client = client
        self.headers = {"User-Agent": f"SONORA/0.2 ( {contact} )", "Accept": "application/json"}
        self.throttle = throttle or Throttle(1.1)

    def find_isrc(self, title: str, artist: str, duration_ms: int | None) -> tuple[str | None, str]:
        """Restituisce (isrc, motivo). Un ISRC viene accettato solo se la corrispondenza è univoca:
        una sola registrazione con punteggio 100, durata entro 2 s e un solo ISRC."""
        q = f'recording:"{_esc(title)}" AND artist:"{_esc(artist)}"'
        self.throttle.wait()
        try:
            r = self.client.get(f"{BASE}/recording", params={"query": q, "fmt": "json", "limit": 5, "inc": "isrcs"},
                                headers=self.headers, timeout=15)
        except httpx.HTTPError as e:
            raise ProviderUnavailable(str(e)) from e
        if r.status_code == 503:
            raise ProviderUnavailable("MusicBrainz: limite di frequenza superato")
        if r.status_code >= 400:
            raise ProviderUnavailable(f"MusicBrainz ha risposto {r.status_code}")
        recs = [x for x in r.json().get("recordings", []) if x.get("score") == 100]
        if duration_ms:
            recs = [x for x in recs if x.get("length") and abs(x["length"] - duration_ms) <= 2000]
        isrcs = {i for x in recs for i in (x.get("isrcs") or [])}
        if len(isrcs) == 1:
            return isrcs.pop(), "match_univoco"
        return None, "nessuna_corrispondenza" if not isrcs else "ambiguo"


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')
