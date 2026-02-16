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


class UserBase(BaseModel):
    code: str
    full_name: str
    email: Optional[str] = None
    role: Literal["student", "teacher", "admin"]
    academic_plan: Optional[str] = None
    semester: Optional[str] = None
    allow_multi_session: bool = False
    max_sessions: int = 1
    is_active: bool = True


class UserCreateRequest(UserBase):
    password: str = Field(min_length=6)


class UserPatchRequest(BaseModel):
    code: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Literal["student", "teacher", "admin"]] = None
    academic_plan: Optional[str] = None
    semester: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6)
    allow_multi_session: Optional[bool] = None
    max_sessions: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    source: str
    created_at: datetime
    updated_at: datetime


class CsvImportResponse(BaseModel):
    import_id: int
    status: Literal["processing", "success", "partial", "failed"]
    summary: dict = Field(default_factory=dict)


class CsvImportListItem(BaseModel):
    import_id: int
    filename: str
    status: Literal["processing", "success", "partial", "failed"]
    started_at: datetime
    ended_at: Optional[datetime] = None
    summary: dict = Field(default_factory=dict)


class CsvImportRowError(BaseModel):
    row_number: int
    error_message: str
    raw_data: dict = Field(default_factory=dict)


class CsvImportDetailResponse(BaseModel):
    import_id: int
    filename: str
    status: Literal["processing", "success", "partial", "failed"]
    started_at: datetime
    ended_at: Optional[datetime] = None
    summary: dict = Field(default_factory=dict)
    error_rows: list[CsvImportRowError] = Field(default_factory=list)


class GlpiSyncStartRequest(BaseModel):
    mode: Literal["manual", "scheduled"]


class GlpiSyncStartResponse(BaseModel):
    run_id: int
    status: Literal["processing", "success", "partial", "failed"]


class GlpiSyncStatusResponse(BaseModel):
    run_id: int
    mode: Literal["manual", "scheduled"]
    status: Literal["processing", "success", "partial", "failed"]
    started_at: datetime
    ended_at: Optional[datetime] = None
    summary: dict = Field(default_factory=dict)


class GlpiSyncRunListItem(BaseModel):
    run_id: int
    mode: Literal["manual", "scheduled"]
    status: Literal["processing", "success", "partial", "failed"]
    started_at: datetime
    ended_at: Optional[datetime] = None
    summary: dict = Field(default_factory=dict)
