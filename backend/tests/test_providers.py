import httpx
import pytest

from app.catalog.normalize import normalize
from app.providers.base import ProviderUnavailable
from app.providers.itunes import ItunesAdapter
from app.providers.musicbrainz import MusicBrainzAdapter
from app.providers.throttle import Throttle

SEARCH = {"resultCount": 2, "results": [
    {"wrapperType": "track", "kind": "song", "trackId": 111, "artistId": 9, "collectionId": 77,
     "artistName": "Mina", "collectionName": "Album", "trackName": "Brava", "previewUrl": "https://audio/p.m4a",
     "artworkUrl100": "https://is1-ssl.mzstatic.com/image/thumb/x/100x100bb.jpg", "releaseDate": "1965-01-01T08:00:00Z",
     "trackTimeMillis": 185000, "primaryGenreName": "Pop", "trackExplicitness": "notExplicit",
     "trackViewUrl": "https://music.apple.com/it/album/brava/77?i=111"},
    {"wrapperType": "track", "kind": "music-video", "trackId": 222, "trackName": "Video"},
]}
CHART = {"feed": {"updated": "Mon, 02 Nov 2026 10:00:00 +0000", "results": [
    {"id": "111", "name": "Brava", "artistName": "Mina"}, {"id": "333", "name": "Altro", "artistName": "X"}]}}


def no_wait():
    return Throttle(0, sleep=lambda s: None)


def adapter(handler):
    return ItunesAdapter(httpx.Client(transport=httpx.MockTransport(handler)), "it", throttle=no_wait())


def test_normalize():
    assert normalize("Ciao (feat. Qualcuno) - Remastered 2011") == "ciao"
    assert normalize("Perché  Sì!") == "perche si"


def test_itunes_search_parses_songs_only():
    seen = {}
    def h(req):
        seen.update(dict(req.url.params))
        return httpx.Response(200, json=SEARCH)
    out = adapter(h).search_tracks("mina", 10)
    assert seen["country"] == "it" and seen["entity"] == "song"
    assert len(out) == 1
    t = out[0]
    assert t.external_id == "111" and t.preview_url and t.genre_name == "Pop"
    assert t.artwork_url.endswith("600x600bb.jpg") and t.release_date.year == 1965


def test_chart_falls_back_to_second_host():
    def h(req):
        if req.url.host == "rss.marketingtools.apple.com":
            return httpx.Response(500)
        return httpx.Response(200, json=CHART)
    chart = adapter(h).chart(100)
    assert [c.rank for c in chart] == [1, 2] and chart[0].external_id == "111"


def test_rate_limit_becomes_provider_unavailable():
    with pytest.raises(ProviderUnavailable):
        adapter(lambda r: httpx.Response(429)).search_tracks("x")
    def boom(req):
        raise httpx.ConnectError("offline")
    with pytest.raises(ProviderUnavailable):
        adapter(boom).search_tracks("x")


def test_throttle_waits_between_calls():
    slept, t = [], [0.0]
    th = Throttle(3.0, sleep=lambda s: slept.append(s), clock=lambda: t[0])
    th.wait(); th.wait()
    assert slept and abs(slept[0] - 3.0) < 1e-6


def test_musicbrainz_requires_unique_match():
    rec = lambda isrc, length=200000: {"score": 100, "length": length, "isrcs": [isrc]}
    def mk(recs):
        c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"recordings": recs})))
        return MusicBrainzAdapter(c, "dev@example.com", throttle=no_wait())
    assert mk([rec("ITA1")]).find_isrc("t", "a", 200500) == ("ITA1", "match_univoco")
    assert mk([rec("ITA1"), rec("ITA2")]).find_isrc("t", "a", 200000)[1] == "ambiguo"
    assert mk([rec("ITA1", 260000)]).find_isrc("t", "a", 200000)[0] is None
    with pytest.raises(ValueError):
        MusicBrainzAdapter(httpx.Client(), "")
