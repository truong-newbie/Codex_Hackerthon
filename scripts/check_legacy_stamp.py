"""Exercise legacy stamping on a temporary SQLite backup, never the source."""

import argparse
import sqlite3
from contextlib import closing
import tempfile
from pathlib import Path

from inspect_db_metadata import inspect
from stamp_legacy_sqlite import LEGACY_REVISION, audit, stamp


def check(source: Path) -> None:
    before = inspect(source)
    with tempfile.TemporaryDirectory(prefix="shiftlens-migration-check-") as directory:
        copy = Path(directory, "legacy.db")
        backup = Path(directory, "verified-backup.db")
        with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as original:
            with closing(sqlite3.connect(copy)) as destination:
                original.backup(destination)
        schema_hash = audit(copy)["schema_sha256"]
        stamp(copy, backup, schema_hash)
        with closing(sqlite3.connect(copy)) as conn:
            version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        assert version == LEGACY_REVISION
        assert audit(backup)["tables"] == before["tables"]
    assert inspect(source) == before
    print("Legacy stamp check passed on an isolated copy; source unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    check(parser.parse_args().source)
