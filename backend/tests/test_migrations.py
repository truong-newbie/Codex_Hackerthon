import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config import settings


def _upgrade(monkeypatch, database: Path, revision: str) -> None:
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{database.as_posix()}")
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, revision)


def test_fresh_database_migrates_to_head(tmp_path, monkeypatch):
    database = tmp_path / "fresh.db"
    _upgrade(monkeypatch, database, "head")
    with closing(sqlite3.connect(database)) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"operations", "audit_events", "training_sessions", "training_results"}.issubset(tables)
        assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "20261114_0002"


def test_legacy_result_is_backfilled_without_rewriting_payload(tmp_path, monkeypatch):
    database = tmp_path / "legacy.db"
    _upgrade(monkeypatch, database, "20261114_0001")
    payload = '{"score":87,"evidence":[{"exact_quote":"Xin lỗi anh"}]}'
    digest_before = hashlib.sha256(payload.encode()).hexdigest()
    with closing(sqlite3.connect(database)) as conn:
        with conn:
            conn.execute("INSERT INTO tenants (id, name) VALUES ('tenant', 'Café')")
            conn.execute(
                "INSERT INTO accounts (id, username, email, password_hash) "
                "VALUES ('user', 'user', 'user@example.com', 'legacy')"
            )
            conn.execute("INSERT INTO memberships (id, user_id, tenant_id, role) VALUES ('member', 'user', 'tenant', 'employee')")
            conn.execute("INSERT INTO sops (id, tenant_id, title, active_version_id) VALUES ('sop', 'tenant', 'SOP', 'version')")
            conn.execute(
                "INSERT INTO sop_versions (id, sop_id, version_no, status, steps_json, rubric_json) "
                "VALUES ('version', 'sop', 1, 'approved', '[]', '[]')"
            )
            conn.execute(
                "INSERT INTO training_sessions "
                "(id, tenant_id, user_id, sop_version_id, module_json, completed) "
                "VALUES ('session', 'tenant', 'user', 'version', '{}', 1)"
            )
            conn.execute(
                "INSERT INTO training_results "
                "(id, session_id, score, passed, critical_failure, payload_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("result", "session", 87, 1, 0, payload),
            )
    _upgrade(monkeypatch, database, "head")
    with closing(sqlite3.connect(database)) as conn:
        state, revision = conn.execute(
            "SELECT state, revision FROM training_sessions WHERE id='session'"
        ).fetchone()
        assert (state, revision) == ("evaluated", 0)
        stored_payload = conn.execute("SELECT payload_json FROM training_results WHERE id='result'").fetchone()[0]
        assert hashlib.sha256(stored_payload.encode()).hexdigest() == digest_before
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
