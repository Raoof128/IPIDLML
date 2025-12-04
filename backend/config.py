"""
Configuration Management

Centralized configuration using pydantic-settings.
Reads from environment variables and .env file.
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # App Info
    APP_NAME: str = "IPI-Shield"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Security
    SECRET_KEY: str = Field(default="changeme_in_production", min_length=8)
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Detection Settings
    DEFAULT_SANITIZATION_MODE: str = "balanced"
    INJECTION_THRESHOLD: float = 0.7
    ENABLE_OCR: bool = True
    ENABLE_BERT: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Model Config
    model_config = SettingsConfigDict(
        env_prefix="IPI_", env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


# Global settings instance
settings = Settings()
