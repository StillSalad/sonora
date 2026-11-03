import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..catalog.visibility import visible_tracks_clause
from ..config import get_settings
from ..db import get_db
from ..errors import ApiError
from ..feed.service import build_page, decode_cursor
from ..models import ListeningEvent, Track, User
from ..security import current_user_optional

router = APIRouter(prefix="/feed", tags=["feed"])

EVENT_TYPES = {"preview_start", "preview_progress", "preview_complete", "skip", "like", "unlike", "save", "unsave",
               "external_open", "search_click", "share"}


@router.get("")
def feed(surface: str = Query("for_you", pattern="^for_you$"), cursor: str | None = None,
         limit: int = Query(10, ge=1, le=25), db: Session = Depends(get_db),
         user: User | None = Depends(current_user_optional)):
    session = decode_cursor(cursor)
    if cursor and not session:
        raise ApiError(400, "invalid_cursor", "Cursore non valido.")
    return build_page(db, session, user, limit, get_settings().store_country)


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
