from functools import lru_cache
from typing import Literal, Self

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
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
    registration_open: bool = True
    jwt_secret_key: SecretStr = SecretStr("")
    jwt_access_token_minutes: int = Field(default=15, ge=1, le=60)
    jwt_refresh_token_days: int = Field(default=30, ge=1, le=90)
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    google_redirect_uri: AnyHttpUrl | None = None
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = ""
    openai_prompt_version: str = "v1"
    openai_timeout_seconds: float = Field(default=30.0, gt=0, le=120)

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

    @model_validator(mode="after")
    def validate_production_secrets(self) -> Self:
        if self.app_env == "production" and len(self.jwt_secret_key.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        configured_origins = [
            origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()
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

    @property
    def food_analysis_enabled(self) -> bool:
        return bool(self.openai_api_key.get_secret_value() and self.openai_model)

    @property
    def google_oauth_enabled(self) -> bool:
        return bool(
            self.google_client_id
            and self.google_client_secret.get_secret_value()
            and self.google_redirect_uri
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
