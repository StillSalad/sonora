from app.catalog.ingest import ingest_track
from app.db import SessionLocal
from app.main import API
from app.providers.base import ProviderUnavailable
from app.providers.registry import get_live_adapter, search_cache
from factories import ext


class FakeAdapter:
    name = "itunes"
    def __init__(self, results=None, fail=False):
        self.results, self.fail, self.calls = results or [], fail, 0
    def search_tracks(self, term, limit=25):
        self.calls += 1
        if self.fail:
            raise ProviderUnavailable("offline")
        return self.results


def use(client, adapter):
    client.app.dependency_overrides[get_live_adapter] = lambda: adapter
    search_cache._d.clear()


def test_local_search_by_title_artist_and_tags(client):
    with SessionLocal() as db:
        ingest_track(db, ext(1, title="Perché sì", artist="Lume", genre="Pop"))
        ingest_track(db, ext(2, title="Altro", artist="Corte", genre="Hip-Hop/Rap"))
        db.commit()
    use(client, None)
    r = client.get(f"{API}/search", params={"q": "perche", "limit": 5}).json()
    assert [t["title"] for t in r["items"]] == ["Perché sì"] and r["live"] == "disabled"
    assert client.get(f"{API}/search", params={"q": "corte"}).json()["items"][0]["title"] == "Altro"
    assert [t["title"] for t in client.get(f"{API}/search", params={"tags": "rap"}).json()["items"]] == ["Altro"]
    assert client.get(f"{API}/search", params={"tags": "rap,pop", "tag_mode": "and"}).json()["items"] == []
    assert len(client.get(f"{API}/search", params={"tags": "rap,pop", "tag_mode": "or"}).json()["items"]) == 2


def test_live_search_ingests_and_caches(client):
    fake = FakeAdapter([ext(5, title="Brano nuovo", artist="Mina")])
    use(client, fake)
    r = client.get(f"{API}/search", params={"q": "mina"}).json()
    assert r["live"] == "ok" and r["items"][0]["artists"][0]["name"] == "Mina"
    r2 = client.get(f"{API}/search", params={"q": "Mina"}).json()
    assert r2["live"] == "cached" and fake.calls == 1


def test_live_search_failure_is_reported(client):
    use(client, FakeAdapter(fail=True))
    r = client.get(f"{API}/search", params={"q": "qualcosa"}).json()
    assert r == {"items": [], "live": "unavailable"}


def test_empty_query_rejected(client):
    assert client.get(f"{API}/search").json()["code"] == "empty_query"


def test_tags_and_genre_pages(client):
    with SessionLocal() as db:
        ingest_track(db, ext(1, genre="Hip-Hop/Rap")); db.commit()
    tags = {t["slug"]: t for t in client.get(f"{API}/tags", params={"category": "genre"}).json()["items"]}
    assert len(tags) == 27 and tags["rap"]["track_count"] == 1 and tags["pop"]["track_count"] == 0
    page = client.get(f"{API}/tags/rap/tracks").json()
    assert page["tag"]["label"] == "Rap" and len(page["items"]) == 1
    assert client.get(f"{API}/tags/nope/tracks").status_code == 404
