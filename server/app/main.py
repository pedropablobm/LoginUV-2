from fastapi import FastAPI

from app.api.v1.routes import router
from app.core_config import settings

app = FastAPI(title=settings.app_name)
app.include_router(router)
