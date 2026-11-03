"""Dati DEMO fittizi per provare l'interfaccia senza rete.

Tutti i titoli iniziano con [DEMO], non hanno copertine, audio né link, e compaiono solo con DEMO_MODE=true.
Uso: python -m app.jobs.seed_demo
"""
import random

from ..catalog.ingest import ingest_track
from ..db import SessionLocal
from ..models import PopularityClass
from ..providers.base import ExternalTrack

ARTISTS = ["Nebbia Blu", "Corte Aurora", "Lume", "I Satelliti", "Vela Nera", "Mira Sol", "Onde Corte", "Polvere di Luna"]
GENRES = ["Pop", "Hip-Hop/Rap", "Alternative", "Dance", "R&B/Soul", "Rock", "Jazz", "Afrobeats"]
WORDS = ["Notte", "Vetro", "Marea", "Cometa", "Asfalto", "Neon", "Aprile", "Riva", "Fuoco", "Sabbia", "Eco", "Satin"]


def main() -> None:
    rnd = random.Random(42)
    with SessionLocal() as db:
        for i in range(60):
            a = ARTISTS[i % len(ARTISTS)]
            ext = ExternalTrack(provider="demo", external_id=f"demo-{i}", title=f"[DEMO] {rnd.choice(WORDS)} {rnd.choice(WORDS).lower()}",
                                artist_name=f"[DEMO] {a}", artist_external_id=f"demo-artist-{a}", album_title=f"[DEMO] Album {i // 6}",
                                album_external_id=f"demo-album-{i // 6}", duration_ms=rnd.randint(140, 260) * 1000,
                                genre_name=GENRES[i % len(GENRES)])
            t = ingest_track(db, ext)
            if i < 40:
                t.popularity_class = PopularityClass.popular
                t.popularity_score = round(1 - i / 80, 3)
                t.popularity_confidence = 0.0
                t.popularity_sources = [{"source": "demo", "note": "dato fittizio, nessuna classifica reale"}]
        db.commit()
    print("60 brani DEMO creati. Avvia il backend con DEMO_MODE=true per vederli.")


if __name__ == "__main__":
    main()
