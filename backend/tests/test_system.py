def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json() == {"status": "ok", "database": "ok"}
    assert "x-request-id" in r.headers and r.headers["x-content-type-options"] == "nosniff"


def test_meta_declares_inactive_features_honestly(client):
    f = client.get("/api/v1/meta").json()["features"]
    assert f["auth"] and f["feed"] and f["search"] and f["previews"]
    assert f["collections"] is False and f["integrations"] is False and f["tags"] is False


def test_error_envelope_on_404(client):
    r = client.get("/api/v1/nope")
    assert r.status_code == 404
    assert set(r.json()) >= {"code", "message", "request_id"}
