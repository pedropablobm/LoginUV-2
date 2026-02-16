# Server API

## Run local
```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

## OpenAPI contract
- Source file: `server/openapi.yaml`

## Database migrations (Alembic)
```powershell
cd server
$env:DATABASE_URL="postgresql+psycopg://loginuv:loginuv@localhost:5432/loginuv"
alembic upgrade head
```
