"""Aggiorna il catalogo da Apple (iTunes Search API + classifiche).

Uso:  python -m app.jobs.ingest                # classifica + 27 generi (~2 minuti, 20 richieste/min)
      python -m app.jobs.ingest --solo-classifica
      python -m app.jobs.ingest --generi rap,indie --per-genere 30
Eseguirlo una volta al giorno (cron o scheduler dell'hosting).
"""
import argparse
import logging

import httpx

from ..config import get_settings
from ..db import SessionLocal
from ..catalog.genres import DISCOVERY_TERMS
from ..catalog.ingest import apply_charts, ingest_track
from ..providers.base import ProviderUnavailable
from ..providers.itunes import ItunesAdapter

log = logging.getLogger("sonora.ingest")


def run(adapter, genres: list[str], per_genre: int, chart_only: bool, chart_size: int = 100,
        countries: list[str] | None = None, home: str | None = None) -> dict:
    s = get_settings()
    countries = countries or [c.strip() for c in s.chart_countries.split(",") if c.strip()]
    home = (home or s.store_country).lower()
    stats = {"chart": 0, "genre_tracks": 0, "countries": {}, "errors": []}
    with SessionLocal() as db:
        charts = []
        for c in countries:
            try:
                entries = adapter.chart(chart_size, country=c)
            except ProviderUnavailable as e:
                stats["errors"].append(f"classifica {c}: {e}")
                continue
            charts += entries
            stats["countries"][c] = len(entries)
        if not charts:
            raise ProviderUnavailable("Nessuna classifica disponibile")
        # lookup sullo store di casa: chi non è disponibile in Italia non torna e viene scartato
        ids = list(dict.fromkeys(e.external_id for e in charts))
        by_ext = {ext.external_id: ingest_track(db, ext) for ext in adapter.lookup_tracks(ids)}
        apply_charts(db, by_ext, charts, home=home)
        db.commit()
        stats["chart"] = len(by_ext)
        log.info("classifiche %s: %s brani", ",".join(stats["countries"]), len(by_ext))
        if chart_only:
            return stats
        for slug in genres:
            try:
                found = adapter.search_tracks(DISCOVERY_TERMS[slug], limit=per_genre)
            except ProviderUnavailable as e:
                stats["errors"].append(f"{slug}: {e}")
                continue
            for ext in found:
                ingest_track(db, ext)
            db.commit()
            stats["genre_tracks"] += len(found)
            log.info("%s: %s brani", slug, len(found))
    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-classifica", action="store_true")
    ap.add_argument("--generi", default=",".join(DISCOVERY_TERMS))
    ap.add_argument("--per-genere", type=int, default=40)
    a = ap.parse_args()
    s = get_settings()
    if not s.itunes_enabled:
        raise SystemExit("ITUNES_ENABLED=false: import disattivato.")
    with httpx.Client(headers={"User-Agent": "SONORA/0.2"}) as client:
        stats = run(ItunesAdapter(client, s.store_country), [g for g in a.generi.split(",") if g in DISCOVERY_TERMS],
                    a.per_genere, a.solo_classifica)
    print(stats)


if __name__ == "__main__":
    main()
