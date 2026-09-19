"""
Application Configuration powered by pydantic-settings.
Reads configuration from environment variables / .env file securely.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "healthcare_ai_evaluation"
    app_env: str = "development"
    app_title: str = "Healthcare AI Evaluation Framework"
    app_version: str = "1.0.0"
    debug: bool = False

    # Optional Gemini / LLM judge config (must remain optional per PRD requirements)
    gemini_api_key: Optional[str] = None
    enable_llm_judge: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


def get_settings() -> Settings:
    """Return an application settings instance."""
    return Settings()


settings = get_settings()
