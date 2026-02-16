from csv import DictReader
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, distinct, func, select
from sqlalchemy.orm import Session
from io import StringIO

from app.db import get_db
from app.models.entities import (
    Campus,
    CsvImport,
    CsvImportRow,
    Event,
    GlpiSyncRun,
    Lab,
    Machine,
    Session as AuthSession,
    User,
)
from app.schemas.dto import (
    BulkEventsRequest,
    CsvImportDetailResponse,
    CsvImportListItem,
    CsvImportRowError,
    CsvImportResponse,
    DashboardSummary,
    GlpiSyncStartRequest,
    GlpiSyncRunListItem,
    GlpiSyncStartResponse,
    GlpiSyncStatusResponse,
    HeartbeatRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    SessionInfo,
    UserCreateRequest,
    UserPatchRequest,
    UserResponse,
)
from app.services.auth import create_access_token, hash_password, verify_password
from app.services.glpi import GlpiSyncError, sync_from_glpi

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        code=user.code,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        academic_plan=user.academic_plan,
        semester=user.semester,
        allow_multi_session=user.allow_multi_session,
        max_sessions=user.max_sessions,
        is_active=user.is_active,
        source=user.source,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "si", "on"}


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(select(User).where(and_(User.code == payload.user_code, User.is_active.is_(True))))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")

    machine = db.scalar(
        select(Machine)
        .join(Lab, Lab.id == Machine.lab_id)
        .join(Campus, Campus.id == Machine.campus_id)
        .where(
            and_(
                Machine.hostname == payload.hostname,
                Machine.is_active.is_(True),
                Lab.code == payload.lab_code,
                Campus.code == payload.campus_code,
            )
        )
    )
    if machine is None:
        raise HTTPException(status_code=404, detail="MACHINE_NOT_REGISTERED")

    active_sessions_count = db.scalar(
        select(func.count(AuthSession.id)).where(
            and_(AuthSession.user_id == user.id, AuthSession.status == "active")
        )
    )
    active_sessions_count = int(active_sessions_count or 0)

    session_limit = max(1, user.max_sessions) if user.allow_multi_session else 1
    if active_sessions_count >= session_limit:
        raise HTTPException(status_code=409, detail="SESSION_LIMIT_REACHED")

    now = datetime.now(timezone.utc)
    session = AuthSession(
        user_id=user.id,
        machine_id=machine.id,
        auth_mode="central",
        status="active",
        start_at=now,
    )
    db.add(session)

    machine.status = "occupied"
    machine.last_seen_at = now

    db.flush()
    db.add(
        Event(
            campus_id=machine.campus_id,
            lab_id=machine.lab_id,
            user_id=user.id,
            machine_id=machine.id,
            session_id=session.id,
            event_type="LOGIN_OK",
            payload={"hostname": machine.hostname},
            created_at=now,
        )
    )

    token = create_access_token(user_code=user.code, session_id=session.id)
    db.commit()

    return LoginResponse(
        access_token=token,
        session=SessionInfo(
            id=session.id,
            user_code=user.code,
            full_name=user.full_name,
            role=user.role,
            machine=machine.hostname,
            auth_mode="central",
        ),
    )


@router.post("/auth/logout", status_code=204)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> Response:
    session = db.scalar(
        select(AuthSession).where(and_(AuthSession.id == payload.session_id, AuthSession.status == "active"))
    )
    if session is None:
        return Response(status_code=204)

    now = datetime.now(timezone.utc)
    session.status = "closed"
    session.end_at = now
    session.close_reason = payload.reason

    machine = db.get(Machine, session.machine_id)
    if machine is not None:
        machine.last_seen_at = now
        active_machine_sessions = db.scalar(
            select(func.count(AuthSession.id)).where(
                and_(AuthSession.machine_id == machine.id, AuthSession.status == "active", AuthSession.id != session.id)
            )
        )
        if int(active_machine_sessions or 0) == 0:
            machine.status = "free"

        db.add(
            Event(
                campus_id=machine.campus_id,
                lab_id=machine.lab_id,
                user_id=session.user_id,
                machine_id=machine.id,
                session_id=session.id,
                event_type="LOGOUT",
                payload={"reason": payload.reason},
                created_at=now,
            )
        )

    db.commit()
    return Response(status_code=204)


@router.post("/client/heartbeat", status_code=202)
def heartbeat(payload: HeartbeatRequest, db: Session = Depends(get_db)) -> Response:
    machine = db.scalar(select(Machine).where(Machine.hostname == payload.hostname))
    if machine is not None:
        machine.last_seen_at = payload.timestamp
        db.add(
            Event(
                campus_id=machine.campus_id,
                lab_id=machine.lab_id,
                machine_id=machine.id,
                session_id=payload.session_id,
                event_type="HEARTBEAT",
                payload={"os_type": payload.os_type, "uptime_seconds": payload.uptime_seconds},
                created_at=payload.timestamp,
            )
        )
        db.commit()
    return Response(status_code=202)


@router.post("/client/events/bulk", status_code=202)
def events_bulk(payload: BulkEventsRequest, db: Session = Depends(get_db)) -> Response:
    machine = db.scalar(select(Machine).where(Machine.hostname == payload.hostname))
    for item in payload.events:
        db.add(
            Event(
                campus_id=machine.campus_id if machine else None,
                lab_id=machine.lab_id if machine else None,
                machine_id=machine.id if machine else None,
                session_id=item.session_id,
                event_type=item.type,
                payload=item.payload,
                created_at=item.timestamp,
            )
        )
    db.commit()
    return Response(status_code=202)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(campus: str | None = Query(default=None), db: Session = Depends(get_db)) -> DashboardSummary:
    machine_filter = [Machine.is_active.is_(True)]
    if campus:
        machine_filter.append(Campus.code == campus)

    active_sessions_stmt = (
        select(AuthSession.machine_id, AuthSession.user_id)
        .join(Machine, Machine.id == AuthSession.machine_id)
        .join(Campus, Campus.id == Machine.campus_id)
        .where(and_(AuthSession.status == "active", *machine_filter))
    )
    active_sessions_subquery = active_sessions_stmt.subquery()

    occupied = int(db.scalar(select(func.count(distinct(active_sessions_subquery.c.machine_id)))) or 0)
    connected_users = int(db.scalar(select(func.count(distinct(active_sessions_subquery.c.user_id)))) or 0)
    machines_total = int(
        db.scalar(
            select(func.count(Machine.id))
            .join(Campus, Campus.id == Machine.campus_id)
            .where(and_(*machine_filter))
        )
        or 0
    )

    return DashboardSummary(
        connected_users=connected_users,
        machines_occupied=occupied,
        machines_free=max(machines_total - occupied, 0),
        alerts=0,
        generated_at=datetime.now(tz=timezone.utc),
    )


@router.get("/dashboard/labs/{campus_code}/{lab_code}")
def dashboard_lab_status(campus_code: str, lab_code: str, db: Session = Depends(get_db)) -> dict:
    lab = db.scalar(
        select(Lab)
        .join(Campus, Campus.id == Lab.campus_id)
        .where(and_(Campus.code == campus_code, Lab.code == lab_code))
    )
    if lab is None:
        raise HTTPException(status_code=404, detail="LAB_NOT_FOUND")

    machines = db.scalars(select(Machine).where(Machine.lab_id == lab.id).order_by(Machine.hostname.asc())).all()
    payload_machines: list[dict] = []
    for machine in machines:
        active_session = db.scalar(
            select(AuthSession).where(and_(AuthSession.machine_id == machine.id, AuthSession.status == "active"))
        )
        active_user = db.get(User, active_session.user_id) if active_session else None
        payload_machines.append(
            {
                "hostname": machine.hostname,
                "status": machine.status,
                "user_code": active_user.code if active_user else None,
                "session_start": active_session.start_at if active_session else None,
            }
        )

    return {"campus_code": campus_code, "lab_code": lab_code, "machines": payload_machines}


@router.get("/users", response_model=list[UserResponse])
def users_list(active: bool | None = Query(default=None), db: Session = Depends(get_db)) -> list[UserResponse]:
    stmt = select(User).order_by(User.id.asc())
    if active is not None:
        stmt = stmt.where(User.is_active.is_(active))
    users = db.scalars(stmt).all()
    return [_to_user_response(user) for user in users]


@router.post("/users", status_code=201, response_model=UserResponse)
def users_create(payload: UserCreateRequest, db: Session = Depends(get_db)) -> UserResponse:
    if payload.max_sessions < 1:
        raise HTTPException(status_code=422, detail="INVALID_MAX_SESSIONS")

    exists = db.scalar(select(User.id).where(User.code == payload.code))
    if exists is not None:
        raise HTTPException(status_code=409, detail="USER_CODE_ALREADY_EXISTS")

    user = User(
        code=payload.code,
        full_name=payload.full_name,
        email=payload.email,
        role=payload.role,
        academic_plan=payload.academic_plan,
        semester=payload.semester,
        password_hash=hash_password(payload.password),
        allow_multi_session=payload.allow_multi_session,
        max_sessions=payload.max_sessions if payload.allow_multi_session else 1,
        is_active=payload.is_active,
        source="local",
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


@router.patch("/users/{id}", response_model=UserResponse)
def users_patch(id: int, payload: UserPatchRequest, db: Session = Depends(get_db)) -> UserResponse:
    user = db.get(User, id)
    if user is None:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    body = payload.model_dump(exclude_unset=True)
    if "max_sessions" in body and body["max_sessions"] is not None and body["max_sessions"] < 1:
        raise HTTPException(status_code=422, detail="INVALID_MAX_SESSIONS")

    if "code" in body and body["code"] != user.code:
        exists = db.scalar(select(User.id).where(and_(User.code == body["code"], User.id != user.id)))
        if exists is not None:
            raise HTTPException(status_code=409, detail="USER_CODE_ALREADY_EXISTS")

    for field in ("code", "full_name", "email", "role", "academic_plan", "semester", "is_active"):
        if field in body:
            setattr(user, field, body[field])

    if "password" in body and body["password"]:
        user.password_hash = hash_password(body["password"])
    if "allow_multi_session" in body:
        user.allow_multi_session = bool(body["allow_multi_session"])
    if "max_sessions" in body and body["max_sessions"] is not None:
        user.max_sessions = int(body["max_sessions"])
    if not user.allow_multi_session:
        user.max_sessions = 1

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


@router.post("/users/import-csv", status_code=202, response_model=CsvImportResponse)
def users_import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> CsvImportResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="FILENAME_REQUIRED")

    csv_import = CsvImport(filename=file.filename, status="processing", summary={})
    db.add(csv_import)
    db.flush()

    created = 0
    updated = 0
    errors = 0
    processed = 0

    content = file.file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="INVALID_CSV_ENCODING") from exc

    reader = DictReader(text.splitlines())
    required_fields = {"code", "full_name", "role", "password"}
    if reader.fieldnames is None or not required_fields.issubset(set(reader.fieldnames)):
        raise HTTPException(status_code=400, detail="INVALID_CSV_HEADERS")

    now = datetime.now(timezone.utc)
    for row_number, row in enumerate(reader, start=2):
        processed += 1
        try:
            code = (row.get("code") or "").strip()
            full_name = (row.get("full_name") or "").strip()
            role = (row.get("role") or "").strip()
            password = row.get("password") or ""

            if not code or not full_name or role not in {"student", "teacher", "admin"} or not password:
                raise ValueError("Required fields missing or invalid role")

            allow_multi = _parse_bool(row.get("allow_multi_session"), default=False)
            max_sessions = int(row.get("max_sessions") or 1)
            if max_sessions < 1:
                raise ValueError("max_sessions must be >= 1")

            existing = db.scalar(select(User).where(User.code == code))
            if existing is None:
                db.add(
                    User(
                        code=code,
                        full_name=full_name,
                        email=(row.get("email") or None) or None,
                        role=role,
                        academic_plan=(row.get("academic_plan") or None) or None,
                        semester=(row.get("semester") or None) or None,
                        password_hash=hash_password(password),
                        allow_multi_session=allow_multi,
                        max_sessions=max_sessions if allow_multi else 1,
                        is_active=_parse_bool(row.get("is_active"), default=True),
                        source="csv",
                        updated_at=now,
                    )
                )
                created += 1
            else:
                existing.full_name = full_name
                existing.email = (row.get("email") or None) or None
                existing.role = role
                existing.academic_plan = (row.get("academic_plan") or None) or None
                existing.semester = (row.get("semester") or None) or None
                existing.password_hash = hash_password(password)
                existing.allow_multi_session = allow_multi
                existing.max_sessions = max_sessions if allow_multi else 1
                existing.is_active = _parse_bool(row.get("is_active"), default=True)
                existing.source = "csv"
                existing.updated_at = now
                updated += 1

            db.add(
                CsvImportRow(
                    import_id=csv_import.id,
                    row_number=row_number,
                    row_status="ok",
                    raw_data={k: (v or "") for k, v in row.items()},
                )
            )
        except Exception as exc:
            errors += 1
            db.add(
                CsvImportRow(
                    import_id=csv_import.id,
                    row_number=row_number,
                    row_status="error",
                    error_message=str(exc),
                    raw_data={k: (v or "") for k, v in row.items()},
                )
            )

    summary = {"processed": processed, "created": created, "updated": updated, "errors": errors}
    csv_import.summary = summary
    csv_import.ended_at = datetime.now(timezone.utc)
    if errors == 0:
        csv_import.status = "success"
    elif created > 0 or updated > 0:
        csv_import.status = "partial"
    else:
        csv_import.status = "failed"

    db.commit()
    return CsvImportResponse(import_id=csv_import.id, status=csv_import.status, summary=summary)


@router.get("/users/import-csv", response_model=list[CsvImportListItem])
def users_import_csv_list(limit: int = Query(default=20, ge=1, le=200), db: Session = Depends(get_db)) -> list[CsvImportListItem]:
    imports = db.scalars(select(CsvImport).order_by(CsvImport.started_at.desc()).limit(limit)).all()
    return [
        CsvImportListItem(
            import_id=item.id,
            filename=item.filename,
            status=item.status,
            started_at=item.started_at,
            ended_at=item.ended_at,
            summary=item.summary or {},
        )
        for item in imports
    ]


@router.get("/users/import-csv/{import_id}", response_model=CsvImportDetailResponse)
def users_import_csv_detail(import_id: int, db: Session = Depends(get_db)) -> CsvImportDetailResponse:
    csv_import = db.get(CsvImport, import_id)
    if csv_import is None:
        raise HTTPException(status_code=404, detail="CSV_IMPORT_NOT_FOUND")

    error_rows = db.scalars(
        select(CsvImportRow)
        .where(and_(CsvImportRow.import_id == import_id, CsvImportRow.row_status == "error"))
        .order_by(CsvImportRow.row_number.asc())
    ).all()

    return CsvImportDetailResponse(
        import_id=csv_import.id,
        filename=csv_import.filename,
        status=csv_import.status,
        started_at=csv_import.started_at,
        ended_at=csv_import.ended_at,
        summary=csv_import.summary or {},
        error_rows=[
            CsvImportRowError(
                row_number=row.row_number,
                error_message=row.error_message or "Unknown error",
                raw_data=row.raw_data or {},
            )
            for row in error_rows
        ],
    )


@router.get("/users/import-csv/{import_id}/errors.csv")
def users_import_csv_errors_download(import_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    csv_import = db.get(CsvImport, import_id)
    if csv_import is None:
        raise HTTPException(status_code=404, detail="CSV_IMPORT_NOT_FOUND")

    error_rows = db.scalars(
        select(CsvImportRow)
        .where(and_(CsvImportRow.import_id == import_id, CsvImportRow.row_status == "error"))
        .order_by(CsvImportRow.row_number.asc())
    ).all()

    output = StringIO()
    output.write("row_number,error_message,raw_data\n")
    for row in error_rows:
        message = (row.error_message or "Unknown error").replace('"', '""')
        raw_data = str(row.raw_data or {}).replace('"', '""')
        output.write(f'{row.row_number},"{message}","{raw_data}"\n')
    output.seek(0)

    filename = f"import_{import_id}_errors.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(output, media_type="text/csv; charset=utf-8", headers=headers)


@router.post("/integrations/glpi/sync", status_code=202, response_model=GlpiSyncStartResponse)
def glpi_sync(payload: GlpiSyncStartRequest, db: Session = Depends(get_db)) -> GlpiSyncStartResponse:
    run = GlpiSyncRun(run_type=payload.mode, status="processing", summary={})
    db.add(run)
    db.flush()

    try:
        result = sync_from_glpi(db)
        run.status = result.status
        run.summary = result.summary
    except GlpiSyncError as exc:
        run.status = "failed"
        run.summary = {"error": str(exc)}
    except Exception as exc:
        run.status = "failed"
        run.summary = {"error": f"Unexpected sync error: {exc}"}
    finally:
        run.ended_at = datetime.now(timezone.utc)

    db.commit()
    return GlpiSyncStartResponse(run_id=run.id, status=run.status)


@router.get("/integrations/glpi/sync", response_model=list[GlpiSyncRunListItem])
def glpi_sync_list(limit: int = Query(default=20, ge=1, le=200), db: Session = Depends(get_db)) -> list[GlpiSyncRunListItem]:
    runs = db.scalars(select(GlpiSyncRun).order_by(GlpiSyncRun.started_at.desc()).limit(limit)).all()
    return [
        GlpiSyncRunListItem(
            run_id=run.id,
            mode=run.run_type,
            status=run.status,
            started_at=run.started_at,
            ended_at=run.ended_at,
            summary=run.summary or {},
        )
        for run in runs
    ]


@router.get("/integrations/glpi/sync/{run_id}", response_model=GlpiSyncStatusResponse)
def glpi_sync_status(run_id: int, db: Session = Depends(get_db)) -> GlpiSyncStatusResponse:
    run = db.get(GlpiSyncRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="GLPI_SYNC_RUN_NOT_FOUND")
    return GlpiSyncStatusResponse(
        run_id=run.id,
        mode=run.run_type,
        status=run.status,
        started_at=run.started_at,
        ended_at=run.ended_at,
        summary=run.summary or {},
    )


@router.get("/reports/usage")
def report_usage(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    campus: str | None = Query(default=None),
    lab: str | None = Query(default=None),
    user_code: str | None = Query(default=None),
    plan: str | None = Query(default=None),
    semester: str | None = Query(default=None),
    format: str = Query(default="json"),
    db: Session = Depends(get_db),
) -> dict:
    if format != "json":
        return {"status": "not_implemented", "format": format}

    stmt = (
        select(AuthSession)
        .join(User, User.id == AuthSession.user_id)
        .join(Machine, Machine.id == AuthSession.machine_id)
        .join(Lab, Lab.id == Machine.lab_id)
        .join(Campus, Campus.id == Machine.campus_id)
    )
    if from_:
        stmt = stmt.where(AuthSession.start_at >= from_)
    if to:
        stmt = stmt.where(AuthSession.start_at <= to)
    if campus:
        stmt = stmt.where(Campus.code == campus)
    if lab:
        stmt = stmt.where(Lab.code == lab)
    if user_code:
        stmt = stmt.where(User.code == user_code)
    if plan:
        stmt = stmt.where(User.academic_plan == plan)
    if semester:
        stmt = stmt.where(User.semester == semester)

    sessions = db.scalars(stmt).all()
    return {
        "total_sessions": len(sessions),
        "active_sessions": sum(1 for session in sessions if session.status == "active"),
        "generated_at": datetime.now(timezone.utc),
    }


@router.get("/reports/attendance")
def report_attendance(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    plan: str | None = Query(default=None),
    semester: str | None = Query(default=None),
    user_code: str | None = Query(default=None),
    format: str = Query(default="json"),
    db: Session = Depends(get_db),
) -> dict:
    if format != "json":
        return {"status": "not_implemented", "format": format}

    stmt = select(User).where(User.is_active.is_(True))
    if plan:
        stmt = stmt.where(User.academic_plan == plan)
    if semester:
        stmt = stmt.where(User.semester == semester)
    if user_code:
        stmt = stmt.where(User.code == user_code)

    users = db.scalars(stmt).all()
    attendance_rows: list[dict] = []
    for user in users:
        sessions_stmt = select(AuthSession).where(AuthSession.user_id == user.id)
        if from_:
            sessions_stmt = sessions_stmt.where(AuthSession.start_at >= from_)
        if to:
            sessions_stmt = sessions_stmt.where(AuthSession.start_at <= to)
        user_sessions = db.scalars(sessions_stmt).all()
        attendance_rows.append({"user_code": user.code, "full_name": user.full_name, "sessions": len(user_sessions)})

    return {"rows": attendance_rows, "generated_at": datetime.now(timezone.utc)}
