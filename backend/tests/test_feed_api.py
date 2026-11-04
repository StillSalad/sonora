from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.catalog.ingest import apply_chart, ingest_track
from app.config import get_settings
from app.db import SessionLocal
from app.models import Preview, Provider
from app.providers.base import ChartEntry
from conftest import H, register
from factories import ext

GENRES = ["Pop", "Hip-Hop/Rap", "Alternative", "Dance", "Rock", "Jazz"]


def seed(n_pop=45, n_disc=20):
    with SessionLocal() as db:
        by, chart = {}, []
        for i in range(n_pop):
            t = ingest_track(db, ext(i, artist=f"Pop {i % 15}", genre=GENRES[i % 6]))
            by[str(1000 + i)] = t
            chart.append(ChartEntry("itunes", "apple_music_most_played", "it", i + 1, str(1000 + i), "", ""))
        for i in range(n_pop, n_pop + n_disc):
            ingest_track(db, ext(i, artist=f"Indie {i % 8}", genre=GENRES[i % 6]))
        apply_chart(db, by, chart)
        db.commit()


def test_feed_pages_follow_80_20_without_repeats(client):
    seed()
    seen, cursor, slots = [], None, []
    for _ in range(5):
        r = client.get("/api/v1/feed", params={"limit": 10, **({"cursor": cursor} if cursor else {})})
        assert r.status_code == 200, r.text
        body = r.json()
        seen += [it["track"]["id"] for it in body["items"]]
        slots += [it["slot"] for it in body["items"]]
        cursor = body["next_cursor"]
    assert len(seen) == 50 and len(set(seen)) == 50
    assert slots.count("discovery") == 10
    assert body["window"] == {"size": 50, "popular": 40, "discovery": 10, "target": {"popular": 40, "discovery": 10, "of": 50}}


def test_feed_item_shape_and_explanations(client):
    seed(10, 5)
    items = client.get("/api/v1/feed", params={"limit": 5}).json()["items"]
    first = items[0]
    assert first["explanation"].startswith("Popolare in Italia: n.")
    disc = [i for i in items if i["slot"] == "discovery"][0]
    assert disc["explanation"].startswith("Scoperta")
    t = first["track"]
    assert t["preview"]["status"] == "AVAILABLE" and t["preview"]["url"] and t["preview"]["duration_seconds"] == 30
    assert t["links"][0]["label"] == "Ascolta su Apple Music"
    assert t["artwork"]["attribution"] == "Apple Music"


def test_preview_url_hidden_unless_rights_valid(client):
    seed(3, 0)
    with SessionLocal() as db:
        pvs = db.scalars(select(Preview)).all()
        pvs[0].expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        pvs[1].territories = ["US"]
        db.commit()
        ids = [str(p.track_id) for p in pvs]
    a = client.get(f"/api/v1/tracks/{ids[0]}").json()["preview"]
    b = client.get(f"/api/v1/tracks/{ids[1]}").json()["preview"]
    assert a == {"status": "RIGHTS_PENDING", "url": None, "duration_seconds": None, "provider": "itunes"}
    assert b["status"] == "UNAVAILABLE" and b["url"] is None
    with SessionLocal() as db:
        db.scalar(select(Provider).where(Provider.name == "itunes")).enabled = False
        db.commit()
    assert client.get(f"/api/v1/tracks/{ids[2]}").status_code == 404  # provider spento: traccia non mostrata


def test_demo_tracks_hidden_unless_demo_mode(client, monkeypatch):
    with SessionLocal() as db:
        ingest_track(db, ext(1, provider="demo")); db.commit()
    assert client.get("/api/v1/feed").json()["items"] == []
    monkeypatch.setattr(get_settings(), "demo_mode", True)
    items = client.get("/api/v1/feed").json()["items"]
    assert len(items) == 1 and items[0]["track"]["demo"] is True and items[0]["track"]["preview"]["url"] is None


def test_invalid_cursor_and_events(client):
    seed(2, 0)
    assert client.get("/api/v1/feed", params={"cursor": "zzz"}).json()["code"] == "invalid_cursor"
    tid = client.get("/api/v1/feed").json()["items"][0]["track"]["id"]
    ok = client.post("/api/v1/feed/events", json={"track_id": tid, "event_type": "skip"}, headers=H)
    assert ok.status_code == 202
    bad = client.post("/api/v1/feed/events", json={"track_id": tid, "event_type": "hack"}, headers=H)
    assert bad.json()["code"] == "invalid_event"


def test_likes_and_taste_explanation(client):
    seed(12, 4)
    items = client.get("/api/v1/feed", params={"limit": 5}).json()["items"]
    tid = items[0]["track"]["id"]
    assert client.post(f"/api/v1/tracks/{tid}/like", headers=H).status_code == 401
    register(client)
    assert client.post(f"/api/v1/tracks/{tid}/like", headers=H).status_code == 204
    assert client.get(f"/api/v1/tracks/{tid}").json()["liked"] is True
    assert [t["id"] for t in client.get("/api/v1/me/likes").json()["items"]] == [tid]
    reasons = [r for it in client.get("/api/v1/feed", params={"limit": 10}).json()["items"] for r in it["reasons"]]
    assert any(r.startswith("Perché ti piace il genere") for r in reasons)
    assert client.request("DELETE", f"/api/v1/tracks/{tid}/like", headers=H).status_code == 204
    assert client.get("/api/v1/me/likes").json()["items"] == []


DEV = {"X-Sonora-Device": "dispositivo-di-prova-0001"}


def first_page(client, headers=None, n=10):
    return [it["track"]["id"] for it in client.get("/api/v1/feed", params={"limit": n}, headers=headers or {}).json()["items"]]


def test_reopening_app_does_not_repeat_recent_songs(client):
    seed(120, 40)  # catalogo ampio: 120 popolari, 40 scoperte
    seen = []
    for _ in range(4):  # quattro aperture dell'app, ognuna una sessione nuova
        seen += first_page(client, DEV)
    assert len(seen) == 40 and len(set(seen)) == 40  # nessuna ripetizione tra un'apertura e l'altra
    other = first_page(client, {"X-Sonora-Device": "altro-dispositivo-0002"})
    assert len(other) == 10  # un altro dispositivo non è influenzato


def test_small_catalog_still_fills_feed_with_penalized_repeats(client):
    seed(8, 3)
    a = first_page(client, DEV, n=10)
    b = first_page(client, DEV, n=10)
    assert len(a) == len(b) == 10  # con pochi brani si ripetono, ma il feed non si svuota


def test_history_follows_account_across_devices(client):
    seed(120, 40)
    register(client)
    a = first_page(client, {"X-Sonora-Device": "telefono-0000000001"})
    b = first_page(client, {"X-Sonora-Device": "computer-0000000002"})
    assert not set(a) & set(b)


def test_invalid_device_header_is_ignored(client):
    seed(10, 3)
    assert client.get("/api/v1/feed", headers={"X-Sonora-Device": "<script>"}).status_code == 200
