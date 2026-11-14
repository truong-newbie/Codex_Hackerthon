"""Print only SQLite schema metadata and row counts; never write to the database."""

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path


def inspect(path: Path) -> dict:
    database = path.resolve(strict=True)
    if not database.is_file():
        raise ValueError("Database path must be a file")
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as conn:
        conn.execute("PRAGMA query_only=ON")
        tables = [
            name for name, kind in conn.execute("SELECT name, type FROM sqlite_master")
            if kind == "table" and not name.startswith("sqlite_")
        ]
        details = {}
        for name in sorted(tables):
            quoted = '"' + name.replace('"', '""') + '"'
            details[name] = {
                "rows": conn.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0],
                "columns": [column[1] for column in conn.execute(f"PRAGMA table_info({quoted})")],
            }
        schema_sql = [
            row[0] or "" for row in conn.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
            )
        ]
        duplicate_queries = {
            "membership_user_tenant": ("memberships", "user_id, tenant_id"),
            "sop_version_number": ("sop_versions", "sop_id, version_no"),
            "session_turn_number": ("turns", "session_id, turn_no"),
        }
        duplicates = {}
        for label, (table, columns) in duplicate_queries.items():
            if table in details:
                duplicates[label] = conn.execute(
                    f"SELECT COUNT(*) FROM (SELECT 1 FROM {table} GROUP BY {columns} HAVING COUNT(*) > 1)"
                ).fetchone()[0]
        active_version_mismatches = None
        if {"sops", "sop_versions"}.issubset(details):
            active_version_mismatches = conn.execute(
                "SELECT COUNT(*) FROM sops AS s LEFT JOIN sop_versions AS v ON v.id = s.active_version_id "
                "WHERE s.active_version_id IS NOT NULL AND "
                "(v.id IS NULL OR v.sop_id != s.id OR v.status != 'approved')"
            ).fetchone()[0]
        return {
            "size_bytes": database.stat().st_size,
            "schema_sha256": hashlib.sha256("\n".join(schema_sql).encode()).hexdigest(),
            "quick_check": conn.execute("PRAGMA quick_check").fetchone()[0],
            "foreign_key_violations": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
            "duplicate_key_groups": duplicates,
            "active_version_mismatches": active_version_mismatches,
            "tables": details,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.database), indent=2))
