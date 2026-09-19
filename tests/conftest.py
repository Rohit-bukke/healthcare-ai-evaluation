"""
Pytest Fixtures for Healthcare AI Evaluation Framework.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings
from simulator.mock_agent import MockHealthcareAgent
from evaluation.engine import EvaluationEngine


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def test_settings():
    """App Settings fixture."""
    return Settings(app_env="test", debug=True)


@pytest.fixture
def mock_agent():
    """MockHealthcareAgent instance fixture."""
    return MockHealthcareAgent()


@pytest.fixture
def eval_engine():
    """EvaluationEngine instance fixture."""
    return EvaluationEngine()
