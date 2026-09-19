"""
Tests for Application Configuration Module.
"""

from app.config import get_settings, Settings


def test_default_settings():
    settings = get_settings()
    assert settings.app_title == "Healthcare AI Evaluation Framework"
    assert settings.app_version == "1.0.0"
    assert isinstance(settings.mongodb_uri, str)
    assert settings.database_name == "healthcare_ai_evaluation"


def test_custom_settings():
    custom = Settings(
        mongodb_uri="mongodb://localhost:27017/test_db",
        database_name="test_db",
        app_env="testing"
    )
    assert custom.app_env == "testing"
    assert custom.database_name == "test_db"
    assert custom.mongodb_uri == "mongodb://localhost:27017/test_db"
