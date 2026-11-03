from app.config import Settings, get_settings
from app.jobs import background
from app.middleware import client_ip
from conftest import H


def test_database_url_normalized():
    assert Settings(database_url="postgres://u:p@h:5432/d").database_url == "postgresql+psycopg://u:p@h:5432/d"
    assert Settings(database_url="postgresql://u:p@h/d").database_url.startswith("postgresql+psycopg://")


def test_client_ip_uses_forwarded_only_when_trusted(monkeypatch):
    class R:
        headers = {"x-forwarded-for": "203.0.113.9, 10.0.0.1"}
        class client: host = "10.0.0.1"
    assert client_ip(R) == "10.0.0.1"
    monkeypatch.setattr(get_settings(), "trust_proxy", True)
    assert client_ip(R) == "203.0.113.9"


def test_internal_ingest_hidden_without_token_and_protected(client, monkeypatch):
    assert client.post("/api/v1/internal/ingest", headers=H).status_code == 404
    monkeypatch.setattr(get_settings(), "ingest_token", "segreto-lungo")
    assert client.post("/api/v1/internal/ingest", headers={**H, "Authorization": "Bearer no"}).status_code == 401
    calls = []
    monkeypatch.setattr(background, "start", lambda chart_only=False: calls.append(chart_only) or True)
    r = client.post("/api/v1/internal/ingest?chart_only=true", headers={**H, "Authorization": "Bearer segreto-lungo"})
    assert r.status_code == 202 and r.json()["started"] is True and calls == [True]
