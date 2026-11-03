import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{_tmp}/test.db"
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app.catalog.bootstrap import ensure_base_data  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import create_app  # noqa: E402

H = {"X-Sonora-Client": "web"}


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ensure_base_data(db)
    with TestClient(create_app(), base_url="http://testserver") as c:
        yield c


def register(c, email="ada@example.com", username="ada", pw="password-lunga-1", **kw):
    body = {"email": email, "username": username, "display_name": "Ada", "password": pw, "confirm_min_age": True}
    body.update(kw)
    return c.post("/api/v1/auth/register", json=body, headers=H)
