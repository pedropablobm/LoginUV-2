from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import and_, distinct, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.entities import Campus, Event, Lab, Machine, Session as AuthSession, User
from app.schemas.dto import (
    BulkEventsRequest,
    DashboardSummary,
    HeartbeatRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    SessionInfo,
)
from app.services.auth import create_access_token, verify_password

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


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
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    occupied = int(
        db.scalar(select(func.count(distinct(AuthSession.machine_id))).where(AuthSession.status == "active")) or 0
    )
    connected_users = int(
        db.scalar(select(func.count(distinct(AuthSession.user_id))).where(AuthSession.status == "active")) or 0
    )
    machines_total = int(db.scalar(select(func.count(Machine.id)).where(Machine.is_active.is_(True))) or 0)

    return DashboardSummary(
        connected_users=connected_users,
        machines_occupied=occupied,
        machines_free=max(machines_total - occupied, 0),
        alerts=0,
        generated_at=datetime.now(tz=timezone.utc),
    )
