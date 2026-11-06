from sqlalchemy import select

from app.catalog.ingest import apply_charts, ingest_track
from app.db import SessionLocal
from app.main import API
from app.models import PopularityClass, Track
from app.providers.base import ChartEntry
from conftest import H, register
from factories import ext

DEV = {**H, "X-Sonora-Device": "telefono-di-prova-000001"}
GENRES = ["Pop", "Hip-Hop/Rap", "Alternative", "Rock", "Jazz"]


def seed(n=60, chart=40):
    with SessionLocal() as db:
        by, entries = {}, []
        for i in range(n):
            t = ingest_track(db, ext(i, artist=f"Artista {i % 20}", genre=GENRES[i % 5]))
            if i < chart:
                by[str(1000 + i)] = t
                entries.append(ChartEntry("itunes", "apple_music_most_played", "it", i + 1, str(1000 + i), "", ""))
        apply_charts(db, by, entries, home="it")
        db.commit()


def feed(client, headers=DEV, **params):
    return client.get(f"{API}/feed", params={"limit": 20, **params}, headers=headers).json()["items"]


def test_onboarding_artists_follow_chosen_genres(client):
    seed()
    r = client.get(f"{API}/onboarding/artists", params={"genres": "rap,jazz"}).json()["items"]
    assert r and {a["genre"] for a in r} == {"rap", "jazz"}
    assert all(a["artwork_url"] for a in r)
    assert client.get(f"{API}/onboarding/artists", params={"genres": "nonesiste"}).status_code == 422


def test_chosen_genres_shape_feed_and_explain_why(client):
    seed()
    items = feed(client, g="jazz")
    jazz = [i for i in items if any(t["slug"] == "jazz" for t in i["track"]["tags"])]
    assert len(jazz) >= 6  # molto più del 20% atteso a caso
    assert any(i["explanation"] == "Perché hai scelto Jazz" for i in jazz)


def test_chosen_artist_explained_by_name(client):
    seed()
    aid = client.get(f"{API}/onboarding/artists", params={"genres": "pop"}).json()["items"][0]
    reasons = [r for i in feed(client, a=aid["id"]) for r in i["reasons"]]
    assert f"Perché hai scelto {aid['name']}" in reasons


def test_preferences_saved_on_account(client):
    seed()
    register(client)
    aid = client.get(f"{API}/onboarding/artists", params={"genres": "rock"}).json()["items"][0]["id"]
    r = client.put(f"{API}/me/preferences", json={"genres": ["rock", "jazz"], "artists": [aid]}, headers=H)
    assert r.status_code == 200 and set(r.json()["genres"]) == {"rock", "jazz"} and r.json()["artists"][0]["id"] == aid
    assert client.put(f"{API}/me/preferences", json={"genres": ["xx"]}, headers=H).json()["code"] == "invalid_genre"
    # senza parametri nel feed valgono quelle salvate sull'account
    reasons = [r for i in feed(client, headers=H) for r in i["reasons"]]
    assert any(r in ("Perché hai scelto Rock", "Perché hai scelto Jazz") for r in reasons)


def test_not_interested_hides_track_and_undo_restores(client):
    seed(30, 20)
    first = feed(client)[0]["track"]
    fb = client.post(f"{API}/feed/feedback", json={"track_id": first["id"], "kind": "not_interested"}, headers=DEV)
    assert fb.status_code == 201
    for _ in range(3):
        assert first["id"] not in [i["track"]["id"] for i in feed(client)]
    assert client.delete(f"{API}/feed/feedback/{fb.json()['id']}", headers=DEV).status_code == 204
    # un altro dispositivo non può annullare la preferenza di questo
    fb2 = client.post(f"{API}/feed/feedback", json={"track_id": first["id"], "kind": "not_interested"}, headers=DEV).json()
    other = {**H, "X-Sonora-Device": "altro-telefono-00000002"}
    assert client.delete(f"{API}/feed/feedback/{fb2['id']}", headers=other).status_code == 404


def test_hide_artist_removes_all_their_songs(client):
    seed()
    t = feed(client)[0]["track"]
    artist = t["artists"][0]["id"]
    client.post(f"{API}/feed/feedback", json={"track_id": t["id"], "kind": "hide_artist"}, headers=DEV)
    for _ in range(3):
        assert artist not in [i["track"]["artists"][0]["id"] for i in feed(client)]


def test_less_genre_lowers_share(client):
    seed(100, 60)
    def jazz_share(headers):
        n = sum(any(t["slug"] == "jazz" for t in i["track"]["tags"]) for _ in range(5) for i in feed(client, headers=headers))
        return n
    tid = next(i["track"]["id"] for i in feed(client) if any(t["slug"] == "jazz" for t in i["track"]["tags"]))
    base = jazz_share({**H, "X-Sonora-Device": "confronto-senza-feedback-1"})
    for _ in range(3):
        r = client.post(f"{API}/feed/feedback", json={"track_id": tid, "kind": "less_genre"}, headers=DEV)
        assert r.json()["genre"] == "Jazz"
    assert jazz_share(DEV) < base


def test_feedback_requires_identity_and_valid_kind(client):
    seed(5, 2)
    tid = feed(client)[0]["track"]["id"]
    assert client.post(f"{API}/feed/feedback", json={"track_id": tid, "kind": "not_interested"}, headers=H).json()["code"] == "no_identity"
    assert client.post(f"{API}/feed/feedback", json={"track_id": tid, "kind": "boh"}, headers=DEV).json()["code"] == "invalid_feedback"


def test_daily_is_stable_for_the_day_and_a_discovery(client):
    seed()
    a = client.get(f"{API}/feed/daily", headers=DEV).json()
    b = client.get(f"{API}/feed/daily", headers=DEV).json()
    assert a["item"]["track"]["id"] == b["item"]["track"]["id"]
    assert a["item"]["explanation"] == "Scoperta del giorno, scelta per te"
    assert a["item"]["track"]["popularity"]["class"] != "popular"
    others = {client.get(f"{API}/feed/daily", headers={**H, "X-Sonora-Device": f"dispositivo-numero-{i:06d}"}).json()["item"]["track"]["id"] for i in range(8)}
    assert len(others) > 1  # persone diverse, scoperte diverse


def test_similar_tracks(client):
    seed()
    seed_id = feed(client)[0]["track"]["id"]
    r = client.get(f"{API}/tracks/{seed_id}/similar", headers=DEV).json()
    ids = [i["track"]["id"] for i in r["items"]]
    assert seed_id not in ids and len(ids) == len(set(ids)) >= 10
    assert all(i["explanation"].startswith(("Stesso artista", "Stesso genere", "Stessa atmosfera")) for i in r["items"])


def test_mood_votes_become_tags_and_show_on_mood_page(client):
    seed(5, 2)
    tid = feed(client)[0]["track"]["id"]
    assert client.put(f"{API}/tracks/{tid}/moods", json={"moods": ["night"]}, headers=H).status_code == 401
    register(client)
    r = client.put(f"{API}/tracks/{tid}/moods", json={"moods": ["night", "dreamy"]}, headers=H).json()
    assert r["voters"] == 1 and {m["slug"] for m in r["moods"]} == {"night", "dreamy"} and r["mine"] == ["dreamy", "night"]
    card = client.get(f"{API}/tracks/{tid}").json()
    assert {t["slug"] for t in card["tags"] if t["category"] == "mood"} == {"night", "dreamy"}
    assert [t["id"] for t in client.get(f"{API}/tags/night/tracks", params={"category": "mood"}).json()["items"]] == [tid]
    client.put(f"{API}/tracks/{tid}/moods", json={"moods": []}, headers=H)  # tolgo il voto
    assert client.get(f"{API}/tags/night/tracks", params={"category": "mood"}).json()["items"] == []
    assert client.put(f"{API}/tracks/{tid}/moods", json={"moods": ["a", "b", "c"]}, headers=H).status_code == 422


def test_removed_chart_hides_tracks_only_from_there(client):
    with SessionLocal() as db:
        t_fr = ingest_track(db, ext(1)); t_it = ingest_track(db, ext(2)); t_both = ingest_track(db, ext(3))
        E = lambda c, r, i: ChartEntry("itunes", "apple_music_most_played", c, r, str(1000 + i), "", "")
        by = {"1001": t_fr, "1002": t_it, "1003": t_both}
        apply_charts(db, by, [E("fr", 1, 1), E("it", 1, 2), E("fr", 2, 3), E("it", 2, 3)], home="it", configured={"it", "fr"})
        db.commit()
        # tolta la Francia: la nuova importazione usa solo l'Italia
        apply_charts(db, by, [E("it", 1, 2), E("it", 2, 3)], home="it", configured={"it"})
        db.commit()
        assert t_fr.hidden_reason == "chart_removed:FR" and t_fr.popularity_class == PopularityClass.unknown
        assert t_it.hidden_reason is None and t_both.hidden_reason is None
        ids = {str(x) for x in db.scalars(select(Track.id).where(Track.hidden_reason.is_(None))).all()}
    assert str(t_fr.id) not in [i["track"]["id"] for i in client.get(f"{API}/feed").json()["items"]]
    assert str(t_fr.id) not in ids
