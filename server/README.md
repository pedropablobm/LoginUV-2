# Server API

## Run local
```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

## GLPI sync environment
Set these variables in `.env` to enable real GLPI synchronization:
- `GLPI_BASE_URL`
- `GLPI_APP_TOKEN`
- `GLPI_USER_TOKEN`
- `GLPI_VERIFY_SSL` (`true`/`false`)
- `GLPI_TIMEOUT_SECONDS`

## OpenAPI contract
- Source file: `server/openapi.yaml`

## Database migrations (Alembic)
```powershell
cd server
$env:DATABASE_URL="postgresql+psycopg://loginuv:loginuv@localhost:5432/loginuv"
alembic upgrade head
```

## Seed data
```powershell
cd server
python scripts/seed.py
```

Default admin:
- user: `admin`
- password: `Admin123*`
