from sqlalchemy import func, select

from app.catalog.ingest import apply_chart, apply_charts, ingest_track
from app.db import SessionLocal
from app.models import DuplicateCandidate, PopularityClass, Preview, PreviewStatus, Tag, Track, TrackTag
from app.providers.base import ChartEntry
from factories import ext


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_same_provider_track_is_updated_not_duplicated(client):
    with SessionLocal() as db:
        a = ingest_track(db, ext(1)); b = ingest_track(db, ext(1)); db.commit()
        assert a.id == b.id and count(db, Track) == 1
        pv = db.scalar(select(Preview))
        assert pv.status == PreviewStatus.AVAILABLE and pv.duration_seconds == 30 and pv.territories == ["IT"]
        assert pv.rights_reference and "promozional" in pv.rights_reference
        tag = db.scalar(select(Tag).join(TrackTag, TrackTag.tag_id == Tag.id))
        assert tag.slug == "pop"


def test_isrc_merges_across_providers(client):
    with SessionLocal() as db:
        a = ingest_track(db, ext(1, isrc="ITABC1234567"))
        b = ingest_track(db, ext(2, provider="demo", title="Diverso", isrc="ITABC1234567"))
        db.commit()
        assert a.id == b.id and count(db, Track) == 1


def test_uncertain_match_creates_review_candidate(client):
    with SessionLocal() as db:
        ingest_track(db, ext(1, title="Notte (feat. Ospite)", artist="Lume"))
        ingest_track(db, ext(2, title="Notte - Remastered", artist="Lume", duration=201_000))
        db.commit()
        assert count(db, Track) == 2  # mai fuse in automatico
        assert count(db, DuplicateCandidate) == 1


def test_preview_states(client):
    with SessionLocal() as db:
        ingest_track(db, ext(1, preview=False)); db.commit()
        assert db.scalar(select(Preview)).status == PreviewStatus.EXTERNAL_ONLY


def test_chart_sets_and_clears_popularity(client):
    with SessionLocal() as db:
        t1 = ingest_track(db, ext(1)); t2 = ingest_track(db, ext(2))
        apply_chart(db, {"1001": t1, "1002": t2}, [ChartEntry("itunes", "apple_music_most_played", "it", 1, "1001", "", ""),
                                                    ChartEntry("itunes", "apple_music_most_played", "it", 2, "1002", "", "")])
        db.commit()
        assert t1.popularity_class == PopularityClass.popular and t1.popularity_score > t2.popularity_score
        assert t1.popularity_sources[0]["rank"] == 1 and t1.popularity_sources[0]["country"] == "IT"
        apply_chart(db, {"1001": t1}, [ChartEntry("itunes", "apple_music_most_played", "it", 1, "1001", "", "")])
        db.commit()
        assert t2.popularity_class == PopularityClass.unknown and t2.popularity_score is None



def test_multi_country_charts_prefer_home_country(client):
    with SessionLocal() as db:
        t1 = ingest_track(db, ext(1)); t2 = ingest_track(db, ext(2)); t3 = ingest_track(db, ext(3))
        E = lambda c, r, i: ChartEntry("itunes", "apple_music_most_played", c, r, str(1000 + i), "", "")
        apply_charts(db, {"1001": t1, "1002": t2, "1003": t3},
                     [E("it", 5, 1), E("us", 1, 1), E("us", 1, 2), E("it", 1, 3)], home="it")
        db.commit()
        assert all(t.popularity_class == PopularityClass.popular for t in (t1, t2, t3))
        assert t1.popularity_sources[0]["country"] == "IT" and t1.popularity_sources[0]["home"] is True
        assert len(t1.popularity_sources) == 2
        assert t3.popularity_score > t2.popularity_score  # n.1 in Italia batte n.1 all'estero
