"""Create the v1.1 schema for fresh installations.

Existing databases must pass the read-only audit and be explicitly stamped at
this revision before applying later migrations. Never run this CREATE revision
against an existing database with these tables.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261114_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(100)),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_accounts_username", "accounts", ["username"], unique=True)
    op.create_index("ix_accounts_email", "accounts", ["email"], unique=True)
    op.create_table(
        "memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "sops",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("active_version_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "sop_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sop_id", sa.String(36), sa.ForeignKey("sops.id"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("steps_json", sa.JSON(), nullable=False),
        sa.Column("rubric_json", sa.JSON(), nullable=False),
        sa.Column("approved_by", sa.String(36)),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "training_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("sop_version_id", sa.String(36), sa.ForeignKey("sop_versions.id"), nullable=False),
        sa.Column("module_json", sa.JSON(), nullable=False),
        sa.Column("completed", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "turns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("training_sessions.id"), nullable=False),
        sa.Column("turn_no", sa.Integer(), nullable=False),
        sa.Column("employee_text", sa.Text(), nullable=False),
        sa.Column("customer_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "training_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("training_sessions.id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("critical_failure", sa.Boolean(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime()),
        sa.UniqueConstraint("session_id"),
    )


def downgrade() -> None:
    raise RuntimeError("Dropping the legacy schema would destroy data; use a verified backup or forward-fix")
