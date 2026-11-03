"""Interfaccia comune dei provider musicali.

Ogni adapter restituisce dati nel formato neutro qui sotto; il catalogo canonico li importa
conservando provider, ID esterno e data di verifica. Nessun adapter scarica audio.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol


@dataclass
class ExternalTrack:
    provider: str
    external_id: str
    title: str
    artist_name: str
    artist_external_id: str | None = None
    album_title: str | None = None
    album_external_id: str | None = None
    release_date: date | None = None
    duration_ms: int | None = None
    isrc: str | None = None
    explicit: str | None = None
    genre_name: str | None = None
    artwork_url: str | None = None
    external_url: str | None = None
    preview_url: str | None = None
    country: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class ChartEntry:
    provider: str
    chart: str
    country: str
    rank: int
    external_id: str
    title: str
    artist_name: str
    updated: str | None = None


class ProviderUnavailable(Exception):
    """Il provider non risponde o ha rifiutato la richiesta (rete, 5xx, limite superato)."""


class CatalogAdapter(Protocol):
    name: str

    def search_tracks(self, term: str, limit: int = 25) -> list[ExternalTrack]: ...
    def lookup_tracks(self, external_ids: list[str]) -> list[ExternalTrack]: ...
