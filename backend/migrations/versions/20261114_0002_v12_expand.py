"""Expand the schema for versioned operations, audit, and data invariants.

Historical result payloads and transcripts are deliberately not rewritten.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261114_0002"
down_revision = "20261114_0001"
branch_labels = None
depends_on = None


def _refuse_conflicting_history() -> None:
    connection = op.get_bind()
    checks = {
        "duplicate memberships": (
            "SELECT COUNT(*) FROM (SELECT 1 FROM memberships "
            "GROUP BY user_id, tenant_id HAVING COUNT(*) > 1) AS conflicts"
        ),
        "duplicate SOP version numbers": (
            "SELECT COUNT(*) FROM (SELECT 1 FROM sop_versions "
            "GROUP BY sop_id, version_no HAVING COUNT(*) > 1) AS conflicts"
        ),
        "duplicate turn numbers": (
            "SELECT COUNT(*) FROM (SELECT 1 FROM turns "
            "GROUP BY session_id, turn_no HAVING COUNT(*) > 1) AS conflicts"
        ),
        "invalid turn numbers": "SELECT COUNT(*) FROM turns WHERE turn_no < 1 OR turn_no > 4",
        "completed sessions without result": (
            "SELECT COUNT(*) FROM training_sessions AS s "
            "LEFT JOIN training_results AS r ON r.session_id = s.id "
            "WHERE s.completed = 1 AND r.id IS NULL"
        ),
        "results attached to incomplete sessions": (
            "SELECT COUNT(*) FROM training_results AS r "
            "JOIN training_sessions AS s ON s.id = r.session_id "
            "WHERE s.completed = 0"
        ),
        "invalid active SOP pointers": (
            "SELECT COUNT(*) FROM sops AS s "
            "LEFT JOIN sop_versions AS v ON v.id = s.active_version_id "
            "WHERE s.active_version_id IS NOT NULL AND "
            "(v.id IS NULL OR v.sop_id != s.id OR v.status != 'approved')"
        ),
    }
    for label, query in checks.items():
        count = connection.execute(sa.text(query)).scalar_one()
        if count:
            raise RuntimeError(f"Migration stopped: {count} {label}. Resolve explicitly; no automatic data deletion.")
    if connection.dialect.name == "sqlite":
        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Migration stopped: {len(violations)} SQLite foreign key violations")


def upgrade() -> None:
    _refuse_conflicting_history()

    op.add_column("accounts", sa.Column("active", sa.Boolean(), nullable=False, server_default="1"))
    op.add_column("accounts", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("memberships", sa.Column("active", sa.Boolean(), nullable=False, server_default="1"))
    op.add_column("sops", sa.Column("archived_at", sa.DateTime()))
    op.add_column("sop_versions", sa.Column("revision", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("sop_versions", sa.Column("base_version_id", sa.String(36)))
    op.add_column("sop_versions", sa.Column("policy_json", sa.JSON()))
    op.add_column("training_sessions", sa.Column("state", sa.String(20), nullable=False, server_default="active"))
    op.add_column("training_sessions", sa.Column("revision", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("training_sessions", sa.Column("busy_operation_id", sa.String(36)))
    op.add_column("training_sessions", sa.Column("execution_profile_json", sa.JSON()))
    op.execute("UPDATE training_sessions SET state = 'evaluated' WHERE id IN (SELECT session_id FROM training_results)")

    op.create_table(
        "operations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("training_sessions.id")),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("idempotency_key", sa.String(80), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("request_revision", sa.Integer()),
        sa.Column("snapshot_json", sa.JSON()),
        sa.Column("lease_token", sa.String(36)),
        sa.Column("lease_until", sa.DateTime()),
        sa.Column("response_json", sa.JSON()),
        sa.Column("error_code", sa.String(40)),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.add_column("turns", sa.Column("operation_id", sa.String(36)))
    op.add_column("training_results", sa.Column("operation_id", sa.String(36)))
    op.add_column("training_results", sa.Column("scoring_version", sa.String(30)))
    op.add_column("training_results", sa.Column("evidence_schema_version", sa.String(30)))
    op.add_column("training_results", sa.Column("transcript_revision", sa.Integer()))
    op.add_column("training_results", sa.Column("transcript_sha256", sa.String(64)))

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("resource_type", sa.String(40), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
        sa.Column("request_id", sa.String(36)),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_index("ux_memberships_user_tenant", "memberships", ["user_id", "tenant_id"], unique=True)
    op.create_index("ux_sop_versions_sop_number", "sop_versions", ["sop_id", "version_no"], unique=True)
    op.create_index("ux_turns_session_number", "turns", ["session_id", "turn_no"], unique=True)
    op.create_index("ux_turns_operation", "turns", ["operation_id"], unique=True)
    op.create_index("ux_training_results_operation", "training_results", ["operation_id"], unique=True)
    op.create_index(
        "ux_operations_actor_key", "operations", ["tenant_id", "user_id", "kind", "idempotency_key"], unique=True
    )
    op.create_index("ix_operations_session_status", "operations", ["session_id", "status"])
    op.create_index("ix_training_sessions_tenant_time", "training_sessions", ["tenant_id", "created_at", "id"])
    op.create_index("ix_training_sessions_user_time", "training_sessions", ["user_id", "created_at", "id"])
    op.create_index("ix_audit_events_tenant_time", "audit_events", ["tenant_id", "created_at", "id"])


def downgrade() -> None:
    raise RuntimeError("v1.2 expansion is not safely reversible after new writes; restore or forward-fix instead")
