"""Application settings using pydantic-settings with .env support and env var aliases."""

import os
from typing import Literal, Optional

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and optional .env file.
    """

    # Worker Configuration
    max_concurrent_messages: int = Field(
        10,
        ge=1,
        description="Maximum number of concurrent messages processed by the worker",
        validation_alias=AliasChoices("MAX_CONCURRENT_MESSAGES"),
    )

    # Health Check Configuration
    health_check_host: str = Field(
        "0.0.0.0",
        description="Health check server host",
        validation_alias=AliasChoices("HEALTH_CHECK_HOST"),
    )
    health_check_port: int = Field(
        8080,
        ge=1,
        le=65535,
        description="Health check server port",
        validation_alias=AliasChoices("HEALTH_CHECK_PORT"),
    )

    # Logging Configuration
    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = Field(
        "INFO",
        description="Logging level",
        validation_alias=AliasChoices("LOG_LEVEL"),
    )
    json_logs: bool = Field(
        True,
        description="Enable JSON formatted logs",
        validation_alias=AliasChoices("JSON_LOGS", "STRUCTURED_LOGS"),
    )

    # Application Configuration
    environment: str = Field(
        "production",
        description="Application environment",
        validation_alias=AliasChoices("ENVIRONMENT", "ENV", "APP_ENV"),
    )
    service_name: str = Field(
        "sqs-worker",
        description="Service name",
        validation_alias=AliasChoices("SERVICE_NAME", "SERVICE", "APP_NAME"),
    )

    # BaseSettings configuration
    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        validate_default=True,
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, v: str):
        if isinstance(v, str):
            v = v.strip().upper()
        return v

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Backwards-compatible constructor that reads from environment variables and .env.
        """
        return cls()


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create settings singleton. In test environment, always reload.
    """
    global _settings
    if _settings is None or os.getenv("ENVIRONMENT") == "test":
        _settings = Settings()
    return _settings
