"""Mixer 80/20 deterministico e spiegabile (MASTER_PROMPT §B e §I).

Schema fisso: in ogni blocco di 5 posizioni la quinta è "discovery". Così qualunque finestra
mobile di 50 brani contiene 40 popolari e 10 scoperte. Se un bacino è vuoto si usa l'altro
e lo si dichiara (tolleranza). Nessun brano si ripete nella sessione; lo stesso artista non
torna nelle 3 posizioni successive e lo stesso genere non più di 2 volte di fila, con
allentamento progressivo solo se non ci sono alternative.
"""
import hashlib
from dataclasses import dataclass, field

WINDOW = 50
DISCOVERY_EVERY = 5  # 1 ogni 5 = 20%


def slot_for(position: int) -> str:
    return "discovery" if position % DISCOVERY_EVERY == DISCOVERY_EVERY - 1 else "popular"


@dataclass
class Candidate:
    track_id: str
    artist_id: str
    genres: tuple[str, ...]
    pool: str              # popular | discovery
    base: float            # popolarità o qualità del candidato
    affinity: float = 0.0  # gusti dell'utente
    reasons: list[str] = field(default_factory=list)


def _jitter(session: str, track_id: str) -> float:
    h = hashlib.sha256(f"{session}:{track_id}".encode()).digest()
    return int.from_bytes(h[:4], "big") / 2**32 * 0.15  # piccola variazione stabile per sessione


def rank(cands: list[Candidate], session: str) -> list[Candidate]:
    return sorted(cands, key=lambda c: c.base + c.affinity + _jitter(session, c.track_id), reverse=True)


def _ok(c: Candidate, recent: list[Candidate], artist_gap: int, genre_run: int) -> bool:
    if any(r.artist_id == c.artist_id for r in recent[-artist_gap:]) if artist_gap else False:
        return False
    if genre_run and c.genres and len(recent) >= genre_run:
        last = recent[-genre_run:]
        if all(r.genres and r.genres[0] == c.genres[0] for r in last):
            return False
    return True


def pick(pool: list[Candidate], recent: list[Candidate]) -> Candidate | None:
    # si allenta prima il vincolo sul genere, poi quello sull'artista
    for artist_gap, genre_run in ((3, 2), (3, 0), (1, 0), (0, 0)):
        for c in pool:
            if _ok(c, recent, artist_gap, genre_run):
                return c
    return None


@dataclass
class Picked:
    candidate: Candidate
    position: int
    slot: str           # slot effettivamente usato
    planned: str        # slot previsto dallo schema
    tolerance: bool     # True se il bacino previsto era vuoto


def mix(popular: list[Candidate], discovery: list[Candidate], start: int, count: int,
        recent: list[Candidate], session: str) -> list[Picked]:
    pools = {"popular": rank(popular, session), "discovery": rank(discovery, session)}
    out: list[Picked] = []
    history = list(recent)
    for i in range(count):
        pos = start + i
        planned = slot_for(pos)
        other = "discovery" if planned == "popular" else "popular"
        c = pick(pools[planned], history)
        used = planned
        if c is None:
            c = pick(pools[other], history)
            used = other
        if c is None:
            break
        pools[used].remove(c)
        history.append(c)
        out.append(Picked(c, pos, used, planned, used != planned))
    return out
