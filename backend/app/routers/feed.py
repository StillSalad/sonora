import uuid
from datetime import date

from fastapi import APIRouter, Depends, Header, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..catalog.visibility import visible_tracks_clause
from ..config import get_settings
from ..db import get_db
from ..errors import ApiError
from ..feed.personal import negatives, parse_prefs, resolve_prefs, valid_device
from ..feed.service import build_page, daily_pick, decode_cursor
from ..models import FeedFeedback, ListeningEvent, Tag, Track, TrackArtist, TrackTag, User
from ..security import current_user_optional

router = APIRouter(prefix="/feed", tags=["feed"])

EVENT_TYPES = {"preview_start", "preview_progress", "preview_complete", "skip", "like", "unlike", "save", "unsave",
               "external_open", "search_click", "share", "share_story"}
FEEDBACK_KINDS = {"not_interested", "less_genre", "hide_artist"}


@router.get("")
def feed(surface: str = Query("for_you", pattern="^for_you$"), cursor: str | None = None,
         limit: int = Query(10, ge=1, le=25), g: str | None = Query(None, max_length=400),
         a: str | None = Query(None, max_length=2000), db: Session = Depends(get_db),
         user: User | None = Depends(current_user_optional),
         x_sonora_device: str | None = Header(None, max_length=64)):
    session = decode_cursor(cursor)
    if cursor and not session:
        raise ApiError(400, "invalid_cursor", "Cursore non valido.")
    device = valid_device(x_sonora_device)
    prefs = resolve_prefs(db, user, parse_prefs(g, a))
    return build_page(db, session, user, limit, get_settings().store_country, device, prefs, negatives(db, user, device))


@router.get("/daily")
def daily(g: str | None = Query(None, max_length=400), a: str | None = Query(None, max_length=2000),
          db: Session = Depends(get_db), user: User | None = Depends(current_user_optional),
          x_sonora_device: str | None = Header(None, max_length=64)):
    device = valid_device(x_sonora_device)
    day = date.today().isoformat()
    prefs = resolve_prefs(db, user, parse_prefs(g, a))
    item = daily_pick(db, day, user, device, get_settings().store_country, prefs, negatives(db, user, device))
    return {"date": day, "item": item}


class EventIn(BaseModel):
    track_id: uuid.UUID
    event_type: str
    listened_ms: int | None = Field(None, ge=0, le=60_000)
    session_id: str | None = Field(None, max_length=64)
    source_surface: str | None = Field(None, max_length=32)


@router.post("/events", status_code=202)
def event(body: EventIn, db: Session = Depends(get_db), user: User | None = Depends(current_user_optional)):
    """Registra un segnale. Lo skip è solo un segnale debole, non un 'non mi piace' (MASTER_PROMPT §I)."""
    if body.event_type not in EVENT_TYPES:
        raise ApiError(422, "invalid_event", "Tipo di evento non valido.")
    if not db.scalar(select(Track.id).where(Track.id == body.track_id, visible_tracks_clause())):
        raise ApiError(404, "not_found", "Brano non trovato.")
    db.add(ListeningEvent(user_id=user.id if user else None, track_id=body.track_id, event_type=body.event_type,
                          listened_ms=body.listened_ms, session_id=body.session_id, source_surface=body.source_surface))
    db.commit()
    return {"accepted": True}


class FeedbackIn(BaseModel):
    track_id: uuid.UUID
    kind: str


@router.post("/feedback", status_code=201)
def feedback(body: FeedbackIn, db: Session = Depends(get_db), user: User | None = Depends(current_user_optional),
             x_sonora_device: str | None = Header(None, max_length=64)):
    """Segnale negativo esplicito. Serve un account o un identificativo di dispositivo valido."""
    device = valid_device(x_sonora_device)
    if not user and not device:
        raise ApiError(400, "no_identity", "Impossibile salvare la preferenza su questo dispositivo.")
    if body.kind not in FEEDBACK_KINDS:
        raise ApiError(422, "invalid_feedback", "Tipo di preferenza non valido.")
    t = db.get(Track, body.track_id)
    if not t:
        raise ApiError(404, "not_found", "Brano non trovato.")
    fb = FeedFeedback(user_id=user.id if user else None, device_id=device, kind=body.kind)
    label = None
    if body.kind == "not_interested":
        fb.track_id = t.id
    elif body.kind == "hide_artist":
        fb.artist_id = db.scalar(select(TrackArtist.artist_id).where(TrackArtist.track_id == t.id,
                                                                     TrackArtist.role == "primary"))
        if not fb.artist_id:
            raise ApiError(422, "no_artist", "Artista non trovato.")
    else:
        g = db.execute(select(Tag.slug, Tag.label).join(TrackTag, TrackTag.tag_id == Tag.id)
                       .where(TrackTag.track_id == t.id, Tag.category == "genre")).first()
        if not g:
            raise ApiError(422, "no_genre", "Questo brano non ha un genere.")
        fb.genre_slug, label = g
        fb.track_id = t.id
    db.add(fb)
    db.commit()
    return {"id": str(fb.id), "kind": fb.kind, "genre": label,
            "artist_id": str(fb.artist_id) if fb.artist_id else None}


@router.delete("/feedback/{feedback_id}", status_code=204)
def undo_feedback(feedback_id: uuid.UUID, db: Session = Depends(get_db),
                  user: User | None = Depends(current_user_optional),
                  x_sonora_device: str | None = Header(None, max_length=64)):
    device = valid_device(x_sonora_device)
    owner = []
    if user:
        owner.append(FeedFeedback.user_id == user.id)
    if device:
        owner.append(FeedFeedback.device_id == device)
    fb = db.scalar(select(FeedFeedback).where(FeedFeedback.id == feedback_id, or_(*owner))) if owner else None
    if not fb:
        raise ApiError(404, "not_found", "Preferenza non trovata.")
    db.delete(fb)
    db.commit()
    return Response(status_code=204)
