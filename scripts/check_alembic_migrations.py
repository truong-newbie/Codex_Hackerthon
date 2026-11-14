"""Run Alembic on fresh SQLite and optionally an isolated legacy copy."""

import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / ".deps"))
sys.path.insert(0, str(ROOT / "backend"))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app.config import settings  # noqa: E402
from inspect_db_metadata import inspect  # noqa: E402
from stamp_legacy_sqlite import stamp  # noqa: E402


def _history_digest(database: Path) -> str:
    digest = hashlib.sha256()
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        for table, columns in {
            "training_sessions": "id, tenant_id, user_id, sop_version_id, module_json, completed",
            "turns": "id, session_id, turn_no, employee_text, customer_text",
            "training_results": "id, session_id, score, passed, critical_failure, payload_json",
        }.items():
            for row in conn.execute(f"SELECT {columns} FROM {table} ORDER BY id"):
                digest.update(json.dumps(row, ensure_ascii=False, default=str).encode("utf-8"))
                digest.update(b"\n")
    return digest.hexdigest()


def upgrade(database: Path, revision: str = "head") -> None:
    settings.DATABASE_URL = f"sqlite:///{database.resolve().as_posix()}"
    command.upgrade(Config(str(ROOT / "backend" / "alembic.ini")), revision)


def check(source: Path | None = None) -> None:
    with tempfile.TemporaryDirectory(prefix="shiftlens-alembic-check-") as directory:
        root = Path(directory)
        fresh = root / "fresh.db"
        upgrade(fresh)
        with closing(sqlite3.connect(fresh)) as conn:
            assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "20261114_0002"
            tables = {name for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            assert {"operations", "audit_events", "turns", "training_results"}.issubset(tables)
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

        if source is not None:
            before = inspect(source)
            original_history = _history_digest(source)
            legacy = root / "legacy.db"
            backup = root / "legacy-backup.db"
            with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as original:
                with closing(sqlite3.connect(legacy)) as destination:
                    original.backup(destination)
            stamp(legacy, backup, before["schema_sha256"])
            upgrade(legacy)
            after = inspect(legacy)
            for table, metadata in before["tables"].items():
                assert after["tables"][table]["rows"] == metadata["rows"]
            assert after["quick_check"] == "ok"
            assert after["foreign_key_violations"] == 0
            assert _history_digest(legacy) == original_history
            assert inspect(source) == before
    print("Alembic migration checks passed; source database unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-source", type=Path)
    check(parser.parse_args().legacy_source)
