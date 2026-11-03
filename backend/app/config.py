from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurazione letta da variabili d'ambiente (vedi .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "replace_me"
    database_url: str = "sqlite:///./sonora_dev.db"
    frontend_origin: str = "http://localhost:5173"
    session_days: int = 30
    min_age: int = 14  # età minima per il consenso digitale in Italia

    # Catalogo
    store_country: str = "it"          # storefront Apple e territorio delle anteprime
    itunes_enabled: bool = True        # iTunes Search API: nessuna chiave, uso promozionale
    live_search: bool = True           # se il catalogo locale ha pochi risultati, chiede a iTunes
    musicbrainz_contact: str = ""      # email/URL per lo User-Agent; vuoto = MusicBrainz disattivato
    demo_mode: bool = False            # mostra anche i brani demo fittizi (solo sviluppo)

    # Produzione
    trust_proxy: bool = False          # true dietro Netlify/Render: l'IP reale arriva in X-Forwarded-For
    ingest_token: str = ""             # abilita POST /internal/ingest (job giornaliero da GitHub Actions)
    ingest_on_start: bool = False      # al primo avvio con catalogo vuoto importa da solo la classifica

    @field_validator("database_url")
    @classmethod
    def _db_url(cls, v: str) -> str:
        # Supabase/Render forniscono postgres:// o postgresql://: SQLAlchemy vuole il driver esplicito
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.is_production and s.app_secret_key in ("", "replace_me"):
        raise RuntimeError("APP_SECRET_KEY must be set in production")
    if s.is_production and s.database_url.startswith("sqlite"):
        raise RuntimeError("In produzione serve PostgreSQL: imposta DATABASE_URL")
    return s
