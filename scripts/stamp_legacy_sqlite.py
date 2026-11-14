"""Safely baseline an audited v1.1 SQLite database before Alembic upgrade.

Dry-run by default. --apply requires the reviewed schema hash and a new backup
path; the original database is changed only to add alembic_version.
"""

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from inspect_db_metadata import inspect


LEGACY_REVISION = "20261114_0001"
EXPECTED_COLUMNS = {
    "tenants": {"id", "name", "created_at"},
    "accounts": {"id", "username", "email", "password_hash", "full_name", "created_at"},
    "memberships": {"id", "user_id", "tenant_id", "role", "created_at"},
    "sops": {"id", "tenant_id", "title", "active_version_id", "created_at"},
    "sop_versions": {
        "id", "sop_id", "version_no", "status", "steps_json", "rubric_json",
        "approved_by", "approved_at", "created_at",
    },
    "training_sessions": {
        "id", "tenant_id", "user_id", "sop_version_id", "module_json", "completed", "created_at",
    },
    "turns": {"id", "session_id", "turn_no", "employee_text", "customer_text", "created_at"},
    "training_results": {
        "id", "session_id", "score", "passed", "critical_failure", "payload_json", "created_at",
    },
}


def _logical_digest(conn: sqlite3.Connection) -> str:
    """Compare backup and live rows without printing transcript or account data."""
    digest = hashlib.sha256()
    for table in sorted(EXPECTED_COLUMNS):
        digest.update(table.encode("utf-8"))
        for row in conn.execute(f'SELECT * FROM "{table}" ORDER BY id'):
            digest.update(json.dumps(row, ensure_ascii=False, default=str).encode("utf-8"))
            digest.update(b"\n")
    return digest.hexdigest()


def audit(database: Path) -> dict:
    summary = inspect(database)
    if set(summary["tables"]) != set(EXPECTED_COLUMNS):
        raise RuntimeError("Legacy table list does not match the audited v1.1 schema")
    for table, expected in EXPECTED_COLUMNS.items():
        if set(summary["tables"][table]["columns"]) != expected:
            raise RuntimeError(f"Legacy columns differ in {table}")
    if summary["quick_check"] != "ok" or summary["foreign_key_violations"]:
        raise RuntimeError("SQLite integrity or foreign key check failed")
    if any(summary["duplicate_key_groups"].values()) or summary["active_version_mismatches"]:
        raise RuntimeError("Duplicate keys or active SOP pointer conflicts must be resolved first")
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        mismatches = conn.execute(
            "SELECT COUNT(*) FROM training_sessions AS s LEFT JOIN training_results AS r "
            "ON r.session_id = s.id WHERE (s.completed = 1 AND r.id IS NULL) "
            "OR (s.completed = 0 AND r.id IS NOT NULL)"
        ).fetchone()[0]
        if mismatches:
            raise RuntimeError(f"Found {mismatches} result/session state mismatches")
        for table, required_index in {
            "accounts": {"ix_accounts_username", "ix_accounts_email"},
        }.items():
            indexes = {
                row[1] for row in conn.execute(f"PRAGMA index_list({table})") if row[2]
            }
            if not required_index.issubset(indexes):
                raise RuntimeError(f"Required unique indexes missing from {table}")
    return summary


def stamp(database: Path, backup: Path, expected_schema_sha256: str) -> None:
    database = database.resolve(strict=True)
    backup = backup.resolve()
    if backup == database or backup.exists() or not backup.parent.is_dir():
        raise ValueError("Backup must be a new file in an existing directory, separate from the database")
    before = audit(database)
    if before["schema_sha256"] != expected_schema_sha256:
        raise RuntimeError("Schema hash changed since review; inspect the database again")

    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as source:
        with closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
    backed_up = audit(backup)
    if backed_up["schema_sha256"] != before["schema_sha256"] or backed_up["tables"] != before["tables"]:
        raise RuntimeError("Backup verification failed; original database was not changed")
    with closing(sqlite3.connect(backup.as_uri() + "?mode=ro", uri=True)) as backup_connection:
        backup_digest = _logical_digest(backup_connection)

    with closing(sqlite3.connect(database.as_uri() + "?mode=rw", uri=True, timeout=5)) as conn:
        with conn:
            conn.execute("BEGIN EXCLUSIVE")
            if _logical_digest(conn) != backup_digest:
                raise RuntimeError("Database contents changed while backing up; stamp aborted")
            schema_sql = [
                row[0] or "" for row in conn.execute(
                    "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
                )
            ]
            current_schema_hash = hashlib.sha256("\n".join(schema_sql).encode()).hexdigest()
            if current_schema_hash != before["schema_sha256"]:
                raise RuntimeError("Database schema changed while backing up; stamp aborted")
            current_tables = {
                name: conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                for name in EXPECTED_COLUMNS
            }
            expected_counts = {name: data["rows"] for name, data in before["tables"].items()}
            if current_tables != expected_counts:
                raise RuntimeError("Database changed while backing up; stamp aborted")
            conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
            conn.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (LEGACY_REVISION,))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--expected-schema-sha256")
    args = parser.parse_args()
    if args.apply:
        if not args.backup or not args.expected_schema_sha256:
            parser.error("--apply requires --backup and --expected-schema-sha256")
        stamp(args.database, args.backup, args.expected_schema_sha256)
        print(f"Stamped {LEGACY_REVISION} after verified backup at {args.backup}")
    else:
        result = audit(args.database)
        print(f"Legacy audit passed. Schema SHA-256: {result['schema_sha256']}. No changes made.")
