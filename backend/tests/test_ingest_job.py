from sqlalchemy import func, select

from app.db import SessionLocal
from app.jobs.ingest import run
from app.models import PopularityClass, Track
from app.providers.base import ChartEntry, ProviderUnavailable
from factories import ext


class FakeApple:
    name = "itunes"
    def chart(self, limit):
        return [ChartEntry("itunes", "apple_music_most_played", "it", i + 1, str(1000 + i), "", "") for i in range(5)]
    def lookup_tracks(self, ids):
        return [ext(int(i) - 1000) for i in ids]
    def search_tracks(self, term, limit=25):
        if term == "jazz":
            raise ProviderUnavailable("limite")
        return [ext(100 + len(term) * 10 + k, genre="Hip-Hop/Rap") for k in range(3)]


def test_ingest_job(client):
    stats = run(FakeApple(), ["rap", "jazz"], 3, chart_only=False)
    assert stats["chart"] == 5 and stats["genre_tracks"] == 3 and stats["errors"] == ["jazz: limite"]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Track)) == 8
        assert db.scalar(select(func.count()).select_from(Track).where(Track.popularity_class == PopularityClass.popular)) == 5
