from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "LoginUV API"
    env: str = "dev"
    auth_timeout_seconds: int = 5
    database_url: str = "postgresql+psycopg://loginuv:loginuv@localhost:5432/loginuv"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_in_seconds: int = 900

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()