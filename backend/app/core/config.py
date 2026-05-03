from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://library:library@localhost:5432/library"
    log_format: Literal["json", "console"] = "json"

    @property
    def database_url_async(self) -> str:
        """SQLAlchemy async driver (FastAPI)"""
        u = self.database_url
        if "+psycopg://" in u:
            return u.replace("+psycopg://", "+psycopg_async://", 1)
        return u

    # Comma-separated origins for browser clients (e.g. Vite on :5173). Empty = CORS disabled.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1" # redis
    cache_ttl_book_seconds: int = 60
    cache_ttl_book_list_seconds: int = 30

    jwt_secret_key: str = "change-me-in-production-use-long-random-string-this-here-its-just-a-little-project-hehe"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    loan_reminder_webhook_url: str | None = None
    webhook_timeout_seconds: float = 10.0

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "LaBiblioteca <noreply@labiblioteca.com>"
    smtp_use_tls: bool = True

    @field_validator(
        "smtp_host",
        "smtp_user",
        "smtp_password",
        "loan_reminder_webhook_url",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if v == "":
            return None
        return v

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_origins or not self.cors_origins.strip():
            return []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
