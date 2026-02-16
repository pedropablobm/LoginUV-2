from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Campus(Base):
    __tablename__ = "campuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Lab(Base):
    __tablename__ = "labs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('student','teacher','admin')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(180), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    academic_plan: Mapped[str | None] = mapped_column(String(120), nullable=True)
    semester: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    allow_multi_session: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_sessions: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="local")
    glpi_external_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Machine(Base):
    __tablename__ = "machines"
    __table_args__ = (
        CheckConstraint("os_type IN ('windows','debian')", name="ck_machines_os_type"),
        CheckConstraint("status IN ('free','occupied','offline','maintenance')", name="ck_machines_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campus_id: Mapped[int] = mapped_column(ForeignKey("campuses.id"), nullable=False)
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"), nullable=False)
    hostname: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    asset_tag: Mapped[str | None] = mapped_column(String(80), nullable=True)
    os_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    glpi_external_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("auth_mode IN ('central','relay')", name="ck_sessions_auth_mode"),
        CheckConstraint("status IN ('active','closed','forced')", name="ck_sessions_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), nullable=False)
    auth_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    campus_id: Mapped[int | None] = mapped_column(ForeignKey("campuses.id"), nullable=True)
    lab_id: Mapped[int | None] = mapped_column(ForeignKey("labs.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    machine_id: Mapped[int | None] = mapped_column(ForeignKey("machines.id"), nullable=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CsvImport(Base):
    __tablename__ = "csv_imports"
    __table_args__ = (CheckConstraint("status IN ('processing','success','partial','failed')", name="ck_csv_imports_status"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    imported_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class CsvImportRow(Base):
    __tablename__ = "csv_import_rows"
    __table_args__ = (CheckConstraint("row_status IN ('ok','error','skipped')", name="ck_csv_import_rows_row_status"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("csv_imports.id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    row_status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class GlpiSyncRun(Base):
    __tablename__ = "glpi_sync_runs"
    __table_args__ = (
        CheckConstraint("run_type IN ('manual','scheduled')", name="ck_glpi_sync_runs_run_type"),
        CheckConstraint("status IN ('processing','success','partial','failed')", name="ck_glpi_sync_runs_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
