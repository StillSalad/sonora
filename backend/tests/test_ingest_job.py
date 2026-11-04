from sqlalchemy import func, select

from app.db import SessionLocal
from app.jobs.ingest import run
from app.models import PopularityClass, Track
from app.providers.base import ChartEntry, ProviderUnavailable
from factories import ext


class FakeApple:
    name = "itunes"
    def chart(self, limit, country=None):
        if country == "de":
            raise ProviderUnavailable("giù")
        n = 5 if country == "it" else 3  # le classifiche estere si sovrappongono a quella italiana
        return [ChartEntry("itunes", "apple_music_most_played", country, i + 1, str(1000 + i + (0 if country == "it" else 2)), "", "")
                for i in range(n)]
    def lookup_tracks(self, ids):
        return [ext(int(i) - 1000) for i in ids]
    def search_tracks(self, term, limit=25):
        if term == "jazz":
            raise ProviderUnavailable("limite")
        return [ext(100 + len(term) * 10 + k, genre="Hip-Hop/Rap") for k in range(3)]


def test_ingest_job(client):
    stats = run(FakeApple(), ["rap", "jazz"], 3, chart_only=False, countries=["it", "us", "de"], home="it")
    assert stats["chart"] == 5 and stats["genre_tracks"] == 3
    assert stats["countries"] == {"it": 5, "us": 3} and stats["errors"] == ["classifica de: giù", "jazz: limite"]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Track)) == 8
        assert db.scalar(select(func.count()).select_from(Track).where(Track.popularity_class == PopularityClass.popular)) == 5
