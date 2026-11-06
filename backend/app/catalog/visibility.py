from sqlalchemy import exists, select

from ..config import get_settings
from ..models import Provider, ProviderTrack, Track


def visible_tracks_clause():
    """Tracce mostrabili: collegate ad almeno un provider attivo. I dati demo fittizi solo con DEMO_MODE."""
    cond = (ProviderTrack.track_id == Track.id) & (Provider.id == ProviderTrack.provider_id) & Provider.enabled.is_(True)
    if not get_settings().demo_mode:
        cond = cond & (Provider.name != "demo")
    return Track.hidden_reason.is_(None) & exists(
        select(ProviderTrack.id).join(Provider, Provider.id == ProviderTrack.provider_id).where(cond))
