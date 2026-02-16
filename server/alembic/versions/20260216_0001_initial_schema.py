"""initial schema

Revision ID: 20260216_0001
Revises:
Create Date: 2026-02-16 10:40:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260216_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=30), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_main", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "labs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campus_id", sa.Integer(), sa.ForeignKey("campuses.id"), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.UniqueConstraint("campus_id", "code", name="uq_labs_campus_code"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.String(length=60), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=180), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("academic_plan", sa.String(length=120), nullable=True),
        sa.Column("semester", sa.String(length=20), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("allow_multi_session", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("max_sessions", sa.SmallInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("source", sa.String(length=20), nullable=False, server_default=sa.text("'local'")),
        sa.Column("glpi_external_id", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("role IN ('student','teacher','admin')", name="ck_users_role"),
    )

    op.create_table(
        "machines",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("campus_id", sa.Integer(), sa.ForeignKey("campuses.id"), nullable=False),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id"), nullable=False),
        sa.Column("hostname", sa.String(length=80), nullable=False, unique=True),
        sa.Column("asset_tag", sa.String(length=80), nullable=True),
        sa.Column("os_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'free'")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("glpi_external_id", sa.String(length=80), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("os_type IN ('windows','debian')", name="ck_machines_os_type"),
        sa.CheckConstraint("status IN ('free','occupied','offline','maintenance')", name="ck_machines_status"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("machine_id", sa.BigInteger(), sa.ForeignKey("machines.id"), nullable=False),
        sa.Column("auth_mode", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_reason", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("auth_mode IN ('central','relay')", name="ck_sessions_auth_mode"),
        sa.CheckConstraint("status IN ('active','closed','forced')", name="ck_sessions_status"),
        sa.CheckConstraint(
            "close_reason IS NULL OR close_reason IN ('logout','shutdown','unexpected_shutdown','admin_force','timeout')",
            name="ck_sessions_close_reason",
        ),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("campus_id", sa.Integer(), sa.ForeignKey("campuses.id"), nullable=True),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id"), nullable=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("machine_id", sa.BigInteger(), sa.ForeignKey("machines.id"), nullable=True),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "csv_imports",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("imported_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("filename", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("status IN ('processing','success','partial','failed')", name="ck_csv_imports_status"),
    )

    op.create_table(
        "csv_import_rows",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("import_id", sa.BigInteger(), sa.ForeignKey("csv_imports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("row_status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("row_status IN ('ok','error','skipped')", name="ck_csv_import_rows_row_status"),
    )

    op.create_table(
        "glpi_sync_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("run_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("run_type IN ('manual','scheduled')", name="ck_glpi_sync_runs_run_type"),
        sa.CheckConstraint("status IN ('processing','success','partial','failed')", name="ck_glpi_sync_runs_status"),
    )

    op.create_index("idx_sessions_user_status", "sessions", ["user_id", "status"], unique=False)
    op.create_index("idx_sessions_machine_status", "sessions", ["machine_id", "status"], unique=False)
    op.execute("CREATE INDEX idx_events_created_at ON events (created_at DESC)")
    op.create_index("idx_events_event_type", "events", ["event_type"], unique=False)
    op.create_index("idx_machines_lab_status", "machines", ["lab_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_machines_lab_status", table_name="machines")
    op.drop_index("idx_events_event_type", table_name="events")
    op.execute("DROP INDEX idx_events_created_at")
    op.drop_index("idx_sessions_machine_status", table_name="sessions")
    op.drop_index("idx_sessions_user_status", table_name="sessions")

    op.drop_table("glpi_sync_runs")
    op.drop_table("csv_import_rows")
    op.drop_table("csv_imports")
    op.drop_table("events")
    op.drop_table("sessions")
    op.drop_table("machines")
    op.drop_table("users")
    op.drop_table("labs")
    op.drop_table("campuses")
