"""Application settings using pydantic-settings with .env support and env var aliases."""

import os
from typing import Literal, Optional

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and optional .env file.
    """

    # SQS Configuration
    sqs_queue_url: str = Field(
        ...,
        description="SQS queue URL",
        validation_alias=AliasChoices("SQS_QUEUE_URL", "QUEUE_URL"),
    )
    aws_region: str = Field(
        "us-east-1",
        description="AWS region",
        validation_alias=AliasChoices("AWS_REGION", "AWS_DEFAULT_REGION", "REGION"),
    )
    aws_access_key_id: Optional[str] = Field(
        None,
        description="AWS access key id",
        validation_alias=AliasChoices("AWS_ACCESS_KEY_ID", "AWS_ACCESS_KEY"),
    )
    aws_secret_access_key: Optional[str] = Field(
        None,
        description="AWS secret access key",
        validation_alias=AliasChoices("AWS_SECRET_ACCESS_KEY", "AWS_SECRET_KEY"),
    )
    aws_endpoint_url: Optional[str] = Field(
        None,
        description="AWS endpoint URL (e.g., LocalStack)",
        validation_alias=AliasChoices(
            "AWS_ENDPOINT_URL", "SQS_ENDPOINT", "ENDPOINT_URL"
        ),
    )
    # S3
    s3_bucket_name: str | None = Field(
        None,
        description="S3 bucket name",
        validation_alias=AliasChoices("S3_BUCKET_NAME"),
    )

    # Worker Configuration
    max_concurrent_messages: int = Field(
        10,
        ge=1,
        description="Maximum number of concurrent messages processed by the worker",
        validation_alias=AliasChoices("MAX_CONCURRENT_MESSAGES"),
    )
    wait_time_seconds: int = Field(
        20,
        ge=0,
        le=20,  # SQS long polling max wait time is 20 seconds
        description="Long polling wait time for SQS receive",
        validation_alias=AliasChoices("WAIT_TIME_SECONDS"),
    )
    visibility_timeout: int = Field(
        30,
        ge=0,
        description="SQS visibility timeout, in seconds",
        validation_alias=AliasChoices("VISIBILITY_TIMEOUT"),
    )
    max_number_of_messages: int = Field(
        10,
        ge=1,
        le=10,  # SQS receives up to 10 messages per request
        description="Max number of messages per SQS receive request",
        validation_alias=AliasChoices("MAX_NUMBER_OF_MESSAGES"),
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
