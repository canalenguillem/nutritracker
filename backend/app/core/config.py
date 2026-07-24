from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "NutriTrack AI"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    backend_host: str = "0.0.0.0"
    backend_port: int = Field(default=8000, ge=1, le=65535)
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = ""

    mariadb_host: str = "localhost"
    mariadb_port: int = Field(default=3306, ge=1, le=65535)
    mariadb_database: str = "nutritrack"
    mariadb_user: str = "nutritrack"
    mariadb_password: SecretStr = SecretStr("")

    redis_url: str = "redis://localhost:6379/0"
    healthcheck_timeout_seconds: float = Field(default=3.0, gt=0, le=30)

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        normalized = value.rstrip("/")
        if not normalized.startswith("/"):
            raise ValueError("API prefix must start with a slash")
        return normalized

    @property
    def cors_origin_list(self) -> list[str]:
        configured_origins = [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]
        frontend_origin = self.frontend_url.rstrip("/")
        return list(dict.fromkeys([frontend_origin, *configured_origins]))

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+asyncmy",
            username=self.mariadb_user,
            password=self.mariadb_password.get_secret_value(),
            host=self.mariadb_host,
            port=self.mariadb_port,
            database=self.mariadb_database,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
