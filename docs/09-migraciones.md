# 09. Migrations (Alembic)

## Files
- `server/alembic.ini`
- `server/alembic/env.py`
- `server/alembic/versions/20260216_0001_initial_schema.py`

## Run migration
```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg://loginuv:loginuv@localhost:5432/loginuv"
alembic upgrade head
```

## Rollback
```powershell
alembic downgrade -1
```

## Coverage
Initial migration creates:
- campuses, labs, users, machines, sessions, events
- csv_imports, csv_import_rows
- glpi_sync_runs
- indexes for sessions/events/machines queries
