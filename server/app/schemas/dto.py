from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_code: str
    password: str
    hostname: str
    campus_code: str
    lab_code: str


class SessionInfo(BaseModel):
    id: int
    user_code: str
    full_name: str
    role: Literal["student", "teacher", "admin"]
    machine: str
    auth_mode: Literal["central", "relay"]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    session: SessionInfo


class LogoutRequest(BaseModel):
    session_id: int
    reason: Literal["logout", "shutdown", "unexpected_shutdown", "admin_force"] = "logout"


class HeartbeatRequest(BaseModel):
    hostname: str
    session_id: int
    os_type: Literal["windows", "debian"]
    uptime_seconds: int
    timestamp: datetime


class EventItem(BaseModel):
    type: str
    session_id: Optional[int] = None
    timestamp: datetime
    payload: dict = Field(default_factory=dict)


class BulkEventsRequest(BaseModel):
    hostname: str
    events: list[EventItem]


class DashboardSummary(BaseModel):
    connected_users: int
    machines_occupied: int
    machines_free: int
    alerts: int
    generated_at: datetime
