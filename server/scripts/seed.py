from sqlalchemy import select

from app.db import SessionLocal
from app.models.entities import Campus, Lab, Machine, User
from app.services.auth import hash_password


def seed() -> None:
    db = SessionLocal()
    try:
        campus = db.scalar(select(Campus).where(Campus.code == "SEDE_CENTRAL"))
        if campus is None:
            campus = Campus(code="SEDE_CENTRAL", name="Sede Central", is_main=True)
            db.add(campus)
            db.flush()

        lab = db.scalar(select(Lab).where(Lab.campus_id == campus.id, Lab.code == "LAB-1"))
        if lab is None:
            lab = Lab(campus_id=campus.id, code="LAB-1", name="Laboratorio 1")
            db.add(lab)
            db.flush()

        machine = db.scalar(select(Machine).where(Machine.hostname == "PC-001"))
        if machine is None:
            db.add(
                Machine(
                    campus_id=campus.id,
                    lab_id=lab.id,
                    hostname="PC-001",
                    os_type="windows",
                    status="free",
                )
            )

        admin = db.scalar(select(User).where(User.code == "admin"))
        if admin is None:
            db.add(
                User(
                    code="admin",
                    full_name="Administrador LoginUV",
                    role="admin",
                    password_hash=hash_password("Admin123*"),
                    allow_multi_session=True,
                    max_sessions=5,
                    is_active=True,
                    source="local",
                )
            )

        db.commit()
        print("Seed completed. user=admin password=Admin123*")
    finally:
        db.close()


if __name__ == "__main__":
    seed()