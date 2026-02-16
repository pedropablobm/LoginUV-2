from __future__ import annotations

import json
import secrets
import ssl
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib import error, parse, request

from sqlalchemy import and_, not_, select
from sqlalchemy.orm import Session

from app.core_config import settings
from app.models.entities import Campus, Lab, Machine, User
from app.services.auth import hash_password


class GlpiSyncError(Exception):
    pass


@dataclass
class GlpiSyncResult:
    summary: dict
    status: str


class GlpiClient:
    def __init__(self) -> None:
        if not settings.glpi_base_url or not settings.glpi_app_token or not settings.glpi_user_token:
            raise GlpiSyncError("GLPI credentials are not configured")
        self.base_url = settings.glpi_base_url.rstrip("/")
        self.app_token = settings.glpi_app_token
        self.user_token = settings.glpi_user_token
        self.timeout = settings.glpi_timeout_seconds
        self._ssl_context = None
        if not settings.glpi_verify_ssl:
            self._ssl_context = ssl._create_unverified_context()  # noqa: SLF001

    def _send_json_request(
        self,
        method: str,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict | list:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if params:
            url = f"{url}?{parse.urlencode(params)}"

        req = request.Request(url=url, method=method)
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)

        with request.urlopen(req, timeout=self.timeout, context=self._ssl_context) as response:
            content = response.read().decode("utf-8")
            if not content:
                return {}
            return json.loads(content)

    def _request_with_retries(
        self,
        method: str,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict | list:
        delays = [0, 5, 15, 30]
        last_error: Exception | None = None
        for attempt, delay in enumerate(delays):
            if delay > 0:
                time.sleep(delay)
            try:
                return self._send_json_request(method=method, endpoint=endpoint, headers=headers, params=params)
            except (TimeoutError, error.URLError, error.HTTPError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == len(delays) - 1:
                    break
        raise GlpiSyncError(f"GLPI request failed after retries: {last_error}") from last_error

    def init_session(self) -> str:
        response = self._request_with_retries(
            method="GET",
            endpoint="/apirest.php/initSession",
            headers={"App-Token": self.app_token, "Authorization": f"user_token {self.user_token}"},
        )
        session_token = response.get("session_token") if isinstance(response, dict) else None
        if not session_token:
            raise GlpiSyncError("GLPI initSession response missing session_token")
        return session_token

    def kill_session(self, session_token: str) -> None:
        try:
            self._request_with_retries(
                method="GET",
                endpoint="/apirest.php/killSession",
                headers={"App-Token": self.app_token, "Session-Token": session_token},
            )
        except GlpiSyncError:
            return

    def list_users(self, session_token: str, limit: int = 1000) -> list[dict]:
        response = self._request_with_retries(
            method="GET",
            endpoint="/apirest.php/User",
            headers={"App-Token": self.app_token, "Session-Token": session_token},
            params={"range": f"0-{max(0, limit - 1)}"},
        )
        return response if isinstance(response, list) else []

    def list_computers(self, session_token: str, limit: int = 2000) -> list[dict]:
        response = self._request_with_retries(
            method="GET",
            endpoint="/apirest.php/Computer",
            headers={"App-Token": self.app_token, "Session-Token": session_token},
            params={"range": f"0-{max(0, limit - 1)}"},
        )
        return response if isinstance(response, list) else []


def _normalize_role(raw_role: str | None) -> str:
    value = (raw_role or "").strip().lower()
    if value in {"admin", "administrator"}:
        return "admin"
    if value in {"teacher", "docente", "profesor"}:
        return "teacher"
    return "student"


def _infer_os_type(name: str, item: dict) -> str:
    text = f"{name} {(item.get('operatingsystem') or '')}".lower()
    if "win" in text:
        return "windows"
    return "debian"


def _resolve_default_lab(db: Session) -> tuple[Campus, Lab]:
    campus = db.scalar(select(Campus).where(Campus.is_main.is_(True)).order_by(Campus.id.asc()))
    if campus is None:
        campus = Campus(code="SEDE_CENTRAL", name="Sede Central", is_main=True)
        db.add(campus)
        db.flush()

    lab = db.scalar(select(Lab).where(Lab.campus_id == campus.id).order_by(Lab.id.asc()))
    if lab is None:
        lab = Lab(campus_id=campus.id, code="LAB-GLPI", name="Laboratorio GLPI")
        db.add(lab)
        db.flush()

    return campus, lab


def sync_from_glpi(db: Session) -> GlpiSyncResult:
    now = datetime.now(timezone.utc)
    client = GlpiClient()
    session_token = client.init_session()

    users_created = 0
    users_updated = 0
    users_disabled = 0
    machines_created = 0
    machines_updated = 0
    machines_disabled = 0
    skipped = 0

    try:
        remote_users = client.list_users(session_token=session_token)
        remote_computers = client.list_computers(session_token=session_token)

        glpi_user_ids: set[str] = set()
        for item in remote_users:
            external_id = str(item.get("id") or "").strip()
            code = (item.get("name") or "").strip()
            if not external_id or not code:
                skipped += 1
                continue

            glpi_user_ids.add(external_id)
            first_name = (item.get("firstname") or "").strip()
            last_name = (item.get("realname") or "").strip()
            full_name = f"{first_name} {last_name}".strip() or code
            email = (item.get("email") or "").strip() or None
            role = _normalize_role(item.get("role") or item.get("profile"))
            is_active = str(item.get("is_active", "1")).strip() not in {"0", "false", "False"}
            plan = (item.get("academic_plan") or "").strip() or None
            semester = (item.get("semester") or "").strip() or None

            user = db.scalar(select(User).where(User.code == code))
            if user is None:
                db.add(
                    User(
                        code=code,
                        full_name=full_name,
                        email=email,
                        role=role,
                        academic_plan=plan,
                        semester=semester,
                        password_hash=hash_password(secrets.token_urlsafe(18)),
                        allow_multi_session=False,
                        max_sessions=1,
                        is_active=is_active,
                        source="glpi",
                        glpi_external_id=external_id,
                        updated_at=now,
                    )
                )
                users_created += 1
            else:
                user.full_name = full_name
                user.email = email
                user.role = role
                user.academic_plan = plan
                user.semester = semester
                user.is_active = is_active
                user.source = "glpi"
                user.glpi_external_id = external_id
                user.updated_at = now
                users_updated += 1

        if glpi_user_ids:
            to_disable = db.scalars(
                select(User).where(
                    and_(
                        User.glpi_external_id.is_not(None),
                        User.source == "glpi",
                        not_(User.glpi_external_id.in_(glpi_user_ids)),
                        User.is_active.is_(True),
                    )
                )
            ).all()
            for user in to_disable:
                user.is_active = False
                user.updated_at = now
                users_disabled += 1

        _, default_lab = _resolve_default_lab(db)
        glpi_machine_ids: set[str] = set()
        for item in remote_computers:
            external_id = str(item.get("id") or "").strip()
            hostname = (item.get("name") or "").strip()
            if not external_id or not hostname:
                skipped += 1
                continue

            glpi_machine_ids.add(external_id)
            machine = db.scalar(select(Machine).where(Machine.hostname == hostname))
            asset_tag = (item.get("serial") or "").strip() or None
            os_type = _infer_os_type(hostname, item)

            if machine is None:
                db.add(
                    Machine(
                        campus_id=default_lab.campus_id,
                        lab_id=default_lab.id,
                        hostname=hostname,
                        asset_tag=asset_tag,
                        os_type=os_type,
                        status="free",
                        is_active=True,
                        glpi_external_id=external_id,
                        updated_at=now,
                    )
                )
                machines_created += 1
            else:
                machine.asset_tag = asset_tag
                machine.os_type = os_type
                machine.glpi_external_id = external_id
                machine.is_active = True
                machine.updated_at = now
                machines_updated += 1

        if glpi_machine_ids:
            to_disable_machines = db.scalars(
                select(Machine).where(
                    and_(
                        Machine.glpi_external_id.is_not(None),
                        not_(Machine.glpi_external_id.in_(glpi_machine_ids)),
                        Machine.is_active.is_(True),
                    )
                )
            ).all()
            for machine in to_disable_machines:
                machine.is_active = False
                machine.updated_at = now
                machines_disabled += 1

        summary = {
            "users_created": users_created,
            "users_updated": users_updated,
            "users_disabled": users_disabled,
            "machines_created": machines_created,
            "machines_updated": machines_updated,
            "machines_disabled": machines_disabled,
            "skipped": skipped,
        }
        status = "success"
        if skipped > 0:
            status = "partial"
        return GlpiSyncResult(summary=summary, status=status)
    finally:
        client.kill_session(session_token)
