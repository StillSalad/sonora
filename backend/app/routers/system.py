from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import __version__
from ..config import get_settings
from ..db import get_db

router = APIRouter(tags=["system"])

# Stato reale delle funzioni: il frontend lo legge per non mostrare funzioni non ancora attive come funzionanti.
FEATURES = {
    "auth": True,
    "catalog": True,        # Milestone 2
    "search": True,         # Milestone 2
    "feed": True,           # Milestone 3
    "previews": True,       # Milestone 3 (solo anteprime con diritto verificato)
    "likes": True,          # anticipato per il feed; raccolte complete in Milestone 5
    "genre_pages": True,    # generi dai tag dei provider
    "tags": False,          # tag engine completo e mood: Milestone 4
    "collections": False,   # Milestone 5
    "music_dna": False,     # Milestone 5
    "community": False,     # Milestone 6
    "integrations": False,  # Milestone 7
    "admin": False,         # Milestone 8
}


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@router.get("/meta")
def meta():
    s = get_settings()
    return {"store_country": s.store_country.upper(), "demo_mode": s.demo_mode,"name": "SONORA", "version": __version__, "environment": s.app_env,
            "milestone": 3, "features": FEATURES}
