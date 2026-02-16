from datetime import datetime, timezone
from random import randint

from fastapi import APIRouter, HTTPException, Response

from app.schemas.dto import (
    BulkEventsRequest,
    DashboardSummary,
    HeartbeatRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    SessionInfo,
)

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if not payload.user_code or not payload.password:
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")

    # TODO: Replace with real DB validation + session policy checks.
    fake_session = SessionInfo(
        id=randint(1000, 9999),
        user_code=payload.user_code,
        full_name="Usuario Demo",
        role="student",
        machine=payload.hostname,
        auth_mode="central",
    )
    return LoginResponse(access_token="dev-token", session=fake_session)


@router.post("/auth/logout", status_code=204)
def logout(_: LogoutRequest) -> Response:
    return Response(status_code=204)


@router.post("/client/heartbeat", status_code=202)
def heartbeat(_: HeartbeatRequest) -> Response:
    return Response(status_code=202)


@router.post("/client/events/bulk", status_code=202)
def events_bulk(_: BulkEventsRequest) -> Response:
    return Response(status_code=202)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary() -> DashboardSummary:
    return DashboardSummary(
        connected_users=0,
        machines_occupied=0,
        machines_free=0,
        alerts=0,
        generated_at=datetime.now(tz=timezone.utc),
    )
