import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_and_downgrade(tmp_path):
    url = f"sqlite:///{tmp_path}/m.db"
    env = {"DATABASE_URL": url, "PATH": "/usr/bin:/bin"}
    run = lambda *a: subprocess.run([sys.executable, "-m", "alembic", *a], cwd=ROOT, env=env, capture_output=True, text=True)
    up = run("upgrade", "head")
    assert up.returncode == 0, up.stderr
    tables = set(inspect(create_engine(url)).get_table_names())
    assert {"users", "tracks", "provider_tracks", "previews", "tags", "track_tags", "collections",
            "listening_events", "connected_accounts", "audit_logs"} <= tables
    down = run("downgrade", "base")
    assert down.returncode == 0, down.stderr
