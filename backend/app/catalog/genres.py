"""Corrispondenza tra i generi dei provider e i 27 generi di SONORA (tag con origine 'provider')."""
from .normalize import normalize

GENRE_LABELS = {
    "pop": "Pop", "rap": "Rap", "indie": "Indie", "rock": "Rock", "electronic": "Elettronica", "jazz": "Jazz",
    "classical": "Classica", "latin": "Latina", "rnb": "R&B", "metal": "Metal", "country": "Country", "folk": "Folk",
    "soul": "Soul", "funk": "Funk", "disco": "Disco", "kpop": "K-pop", "afrobeat": "Afrobeat", "reggae": "Reggae",
    "blues": "Blues", "ambient": "Ambient", "house": "House", "techno": "Techno", "drill": "Drill", "trap": "Trap",
    "punk": "Punk", "gospel": "Gospel", "soundtrack": "Colonne sonore",
}
MOOD_LABELS = {
    "energy": "Energia", "happy": "Felice", "party": "Festa", "night": "Notte", "dreamy": "Sognante",
    "romantic": "Romantico", "nostalgic": "Nostalgico", "sad": "Triste", "relax": "Relax", "calm": "Calma",
    "focus": "Concentrazione", "epic": "Epico",
}

# nome genere iTunes normalizzato -> slug SONORA
_ITUNES = {
    "pop": "pop", "italian pop": "pop", "pop latino": "latin", "k pop": "kpop", "j pop": "pop", "teen pop": "pop",
    "hip hop rap": "rap", "hip hop": "rap", "rap": "rap", "italian hip hop rap": "rap", "hip hop rap italiano": "rap",
    "trap": "trap", "drill": "drill", "uk drill": "drill",
    "alternative": "indie", "indie pop": "indie", "indie rock": "indie", "alternativa": "indie", "indie": "indie",
    "rock": "rock", "hard rock": "rock", "rock alternativo": "rock", "metal": "metal", "heavy metal": "metal", "punk": "punk",
    "dance": "electronic", "electronic": "electronic", "elettronica": "electronic", "electronica": "electronic",
    "house": "house", "techno": "techno", "ambient": "ambient", "disco": "disco", "funk": "funk",
    "r b soul": "rnb", "r b": "rnb", "contemporary r b": "rnb", "soul": "soul", "neo soul": "soul",
    "latin": "latin", "latino": "latin", "urbano latino": "latin", "reggaeton": "latin", "musica latina": "latin",
    "jazz": "jazz", "classical": "classical", "classica": "classical", "musica classica": "classical",
    "country": "country", "folk": "folk", "singer songwriter": "folk", "cantautori": "folk", "cantautorale": "folk",
    "reggae": "reggae", "blues": "blues", "afrobeats": "afrobeat", "afro beats": "afrobeat", "afrobeat": "afrobeat",
    "afro pop": "afrobeat", "gospel": "gospel", "christian gospel": "gospel", "christian": "gospel",
    "soundtrack": "soundtrack", "colonne sonore": "soundtrack", "original score": "soundtrack", "colonna sonora": "soundtrack",
}

# termini di ricerca per riempire il bacino "scoperta" di ogni genere
DISCOVERY_TERMS = {
    "pop": "pop", "rap": "rap italiano", "indie": "indie italiano", "rock": "rock", "electronic": "electronic",
    "jazz": "jazz", "classical": "piano classical", "latin": "latin", "rnb": "r&b", "metal": "metal",
    "country": "country", "folk": "folk", "soul": "soul", "funk": "funk", "disco": "disco", "kpop": "k-pop",
    "afrobeat": "afrobeats", "reggae": "reggae", "blues": "blues", "ambient": "ambient", "house": "house music",
    "techno": "techno", "drill": "drill", "trap": "trap", "punk": "punk", "gospel": "gospel", "soundtrack": "soundtrack",
}


def genre_slug(provider_genre: str | None) -> str | None:
    if not provider_genre:
        return None
    return _ITUNES.get(normalize(provider_genre))
