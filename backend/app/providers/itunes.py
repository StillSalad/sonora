"""Adapter per la iTunes Search API e le classifiche Apple Marketing Tools.

Fonti (verificare i termini aggiornati prima del lancio pubblico):
- https://performance-partners.apple.com/search-api : nessuna chiave; contenuti promozionali
  (anteprime 30 s, copertine) solo per promuovere lo store, vicino a un badge dello store;
  circa 20 richieste/minuto, con caching consigliato.
- https://rss.marketingtools.apple.com : classifiche "most played" per paese, nessuna chiave.
"""
from datetime import date

import httpx

from .base import ChartEntry, ExternalTrack, ProviderUnavailable
from .throttle import Throttle

ITUNES_BASE = "https://itunes.apple.com"
PROVIDER = "itunes"
RIGHTS_REFERENCE = ("Apple iTunes Search API, termini Performance Partners: uso promozionale, "
                    "anteprima max 30 s vicino a un badge Apple Music, nessuna copia dell'audio. "
                    "https://performance-partners.apple.com/search-api")
PREVIEW_MAX_SECONDS = 30


def artwork(url: str | None, size: int = 600) -> str | None:
    """Le copertine iTunes arrivano a 100x100: la stessa immagine esiste in altre misure."""
    if not url:
        return None
    return url.replace("100x100bb", f"{size}x{size}bb").replace("100x100", f"{size}x{size}")


def _date(v: str | None) -> date | None:
    try:
        return date.fromisoformat(v[:10]) if v else None
    except ValueError:
        return None


class ItunesAdapter:
    name = PROVIDER

    def __init__(self, client: httpx.Client, country: str = "it", throttle: Throttle | None = None,
                 charts_bases: tuple[str, ...] = ("https://rss.marketingtools.apple.com", "https://rss.applemarketingtools.com")):
        self.client, self.country = client, country.lower()
        self.throttle = throttle or Throttle(3.1)
        self.charts_bases = charts_bases

    def _get(self, url: str, params: dict | None = None) -> dict:
        self.throttle.wait()
        try:
            r = self.client.get(url, params=params, timeout=15)
        except httpx.HTTPError as e:
            raise ProviderUnavailable(f"iTunes non raggiungibile: {e}") from e
        if r.status_code == 403 or r.status_code == 429:
            raise ProviderUnavailable("iTunes ha limitato le richieste: riprova più tardi.")
        if r.status_code >= 400:
            raise ProviderUnavailable(f"iTunes ha risposto {r.status_code}")
        try:
            return r.json()
        except ValueError as e:
            raise ProviderUnavailable("Risposta iTunes non valida") from e

    def _track(self, d: dict) -> ExternalTrack | None:
        if d.get("wrapperType") != "track" or d.get("kind") != "song" or not d.get("trackId"):
            return None
        return ExternalTrack(
            provider=PROVIDER, external_id=str(d["trackId"]), title=d.get("trackName") or "",
            artist_name=d.get("artistName") or "", artist_external_id=str(d["artistId"]) if d.get("artistId") else None,
            album_title=d.get("collectionName"), album_external_id=str(d["collectionId"]) if d.get("collectionId") else None,
            release_date=_date(d.get("releaseDate")), duration_ms=d.get("trackTimeMillis"),
            explicit=d.get("trackExplicitness"), genre_name=d.get("primaryGenreName"),
            artwork_url=artwork(d.get("artworkUrl100")), external_url=d.get("trackViewUrl"),
            preview_url=d.get("previewUrl"), country=self.country, raw={"collectionArtistName": d.get("collectionArtistName")},
        )

    def search_tracks(self, term: str, limit: int = 25) -> list[ExternalTrack]:
        data = self._get(f"{ITUNES_BASE}/search", {"term": term, "media": "music", "entity": "song",
                                                    "limit": max(1, min(limit, 200)), "country": self.country})
        return [t for t in (self._track(d) for d in data.get("results", [])) if t]

    def lookup_tracks(self, external_ids: list[str]) -> list[ExternalTrack]:
        out: list[ExternalTrack] = []
        for i in range(0, len(external_ids), 150):
            chunk = external_ids[i:i + 150]
            data = self._get(f"{ITUNES_BASE}/lookup", {"id": ",".join(chunk), "entity": "song", "country": self.country})
            out += [t for t in (self._track(d) for d in data.get("results", [])) if t]
        return out

    def chart(self, limit: int = 100) -> list[ChartEntry]:
        last: Exception | None = None
        for base in self.charts_bases:
            try:
                data = self._get(f"{base}/api/v2/{self.country}/music/most-played/{min(limit, 100)}/songs.json")
            except ProviderUnavailable as e:
                last = e
                continue
            feed = data.get("feed", {})
            return [ChartEntry(provider=PROVIDER, chart="apple_music_most_played", country=self.country, rank=i + 1,
                               external_id=str(r["id"]), title=r.get("name", ""), artist_name=r.get("artistName", ""),
                               updated=feed.get("updated"))
                    for i, r in enumerate(feed.get("results", [])) if r.get("id")]
        raise ProviderUnavailable(f"Classifiche Apple non disponibili: {last}")
