from conftest import H, register


def test_register_login_me_logout(client):
    r = register(client)
    assert r.status_code == 201, r.text
    assert "password_hash" not in r.json()
    assert client.get("/api/v1/auth/me").json()["username"] == "ada"
    assert client.post("/api/v1/auth/logout", headers=H).status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    r = client.post("/api/v1/auth/login", json={"email": "ADA@example.com", "password": "password-lunga-1"}, headers=H)
    assert r.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200


def test_logout_revokes_server_side(client):
    register(client)
    token = client.cookies.get("sonora_session")
    client.post("/api/v1/auth/logout", headers=H)
    client.cookies.set("sonora_session", token)  # riuso del vecchio cookie
    assert client.get("/api/v1/auth/me").status_code == 401


def test_wrong_password_and_duplicate(client):
    register(client)
    r = client.post("/api/v1/auth/login", json={"email": "ada@example.com", "password": "sbagliata"}, headers=H)
    assert r.status_code == 401 and r.json()["code"] == "invalid_credentials"
    assert register(client).status_code == 409


def test_validation(client):
    r = register(client, username="A B", pw="corta")
    assert r.status_code == 422 and r.json()["code"] == "validation_error"
    assert {f["field"] for f in r.json()["fields"]} == {"username", "password"}


def test_age_confirmation_required(client):
    r = register(client, confirm_min_age=False)
    assert r.status_code == 422 and r.json()["code"] == "age_required"


def test_csrf_header_and_origin(client):
    body = {"email": "x@example.com", "password": "x"}
    assert client.post("/api/v1/auth/login", json=body).json()["code"] == "csrf_header"
    r = client.post("/api/v1/auth/login", json=body, headers={**H, "Origin": "https://evil.example"})
    assert r.json()["code"] == "csrf_origin"


def test_rate_limit_login(client):
    body = {"email": "x@example.com", "password": "x"}
    codes = [client.post("/api/v1/auth/login", json=body, headers=H).status_code for _ in range(11)]
    assert codes[-1] == 429


def test_delete_account_anonymizes(client):
    register(client)
    r = client.request("DELETE", "/api/v1/auth/account", json={"password": "password-lunga-1"}, headers=H)
    assert r.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    # email di nuovo disponibile, login col vecchio account impossibile
    assert client.post("/api/v1/auth/login", json={"email": "ada@example.com", "password": "password-lunga-1"}, headers=H).status_code == 401
    assert register(client).status_code == 201


def test_session_endpoint(client):
    assert client.get("/api/v1/auth/session").json() == {"user": None}
    register(client)
    assert client.get("/api/v1/auth/session").json()["user"]["username"] == "ada"
