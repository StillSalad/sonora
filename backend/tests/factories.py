from app.providers.base import ExternalTrack


def ext(i, *, provider="itunes", title=None, artist=None, genre="Pop", preview=True, isrc=None, duration=200_000,
        country="it", artist_id=None):
    artist = artist or f"Artista {i}"
    return ExternalTrack(
        provider=provider, external_id=str(1000 + i) if provider != "demo" else f"demo-{i}",
        title=title or f"Brano {i}", artist_name=artist, artist_external_id=artist_id or f"a-{artist}",
        album_title=f"Album {i}", album_external_id=f"al-{i}", duration_ms=duration, isrc=isrc, genre_name=genre,
        artwork_url=f"https://is1-ssl.mzstatic.com/image/{i}/600x600bb.jpg",
        external_url=f"https://music.apple.com/it/album/x/{i}?i={1000 + i}",
        preview_url=f"https://audio-ssl.itunes.apple.com/preview/{i}.m4a" if preview else None, country=country)
