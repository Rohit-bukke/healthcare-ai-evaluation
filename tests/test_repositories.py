"""
Tests for Repositories Layer.
"""

from evaluation.repositories.scenario_repo import ScenarioRepository
from evaluation.repositories.evaluation_run_repo import EvaluationRunRepository
from evaluation.repositories.finding_repo import FindingRepository
from app.models.scenario import Scenario
from app.models.evaluation import EvaluationRun
from app.models.finding import Finding, FindingSeverity


def test_scenario_repository_git_dataset_loading():
    repo = ScenarioRepository()
    scenarios = repo.list_all()
    assert len(scenarios) >= 10
    sc01 = repo.get_by_id("SCN-001")
    assert sc01 is not None
    assert sc01.title == "Standard Cardiology Appointment Request"
    assert sc01.category == "appointment_request"


def test_evaluation_run_repository_crud():
    repo = EvaluationRunRepository()
    run = EvaluationRun(run_id="RUN-TEST-001", total_scenarios=5, overall_accuracy=0.8)
    repo.insert(run)

    fetched = repo.get_by_id("RUN-TEST-001")
    assert fetched is not None
    assert fetched.run_id == "RUN-TEST-001"
    assert fetched.total_scenarios == 5
    assert fetched.overall_accuracy == 0.8


def test_finding_repository_crud():
    repo = FindingRepository()
    finding = Finding(
        finding_id="FDG-TEST-001",
        severity=FindingSeverity.CRITICAL,
        category="tool_use",
        title="Malformed Payload",
        description="JSON parse error",
        run_id="RUN-TEST-001"
    )
    repo.insert(finding)

    fetched = repo.get_by_id("FDG-TEST-001")
    assert fetched is not None
    assert fetched.severity == FindingSeverity.CRITICAL

    run_findings = repo.get_by_run_id("RUN-TEST-001")
    assert len(run_findings) >= 1
