from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "LoginUV API"
    env: str = "dev"
    auth_timeout_seconds: int = 5


settings = Settings()
