"""
Tests for Pydantic Domain Models.
"""

from app.models.scenario import Scenario
from app.models.conversation import ConversationTurn, TurnRole
from app.models.tool_call import ToolCall, ToolCallStatus
from app.models.metric import MetricResult
from app.models.finding import Finding, FindingSeverity
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.models.regression import RegressionResult


def test_scenario_model():
    sc = Scenario(
        scenario_id="SCN-100",
        title="Test Scenario",
        description="Test description",
        category="booking",
        initial_prompt="Book an appointment",
        expected_outcome="Confirmed"
    )
    assert sc.scenario_id == "SCN-100"
    assert sc.turn_count == 1
    assert sc.tags == []


def test_tool_call_model():
    tc = ToolCall(
        tool_id="T1",
        tool_name="check_availability",
        arguments={"provider": "Dr. Smith"},
        status=ToolCallStatus.SUCCESS,
        latency_ms=100.0
    )
    assert tc.tool_name == "check_availability"
    assert tc.status == ToolCallStatus.SUCCESS
    assert tc.arguments["provider"] == "Dr. Smith"


def test_conversation_turn_model():
    turn = ConversationTurn(
        turn_id="TRN-01",
        role=TurnRole.USER,
        content="Hello Doctor"
    )
    assert turn.turn_id == "TRN-01"
    assert turn.role == TurnRole.USER


def test_evaluation_models():
    metric = MetricResult(metric_name="Accuracy", score=1.0, status="pass")
    finding = Finding(
        finding_id="FDG-1",
        severity=FindingSeverity.HIGH,
        category="safety",
        title="Test Finding",
        description="Description"
    )
    result = EvaluationResult(
        result_id="RES-01",
        run_id="RUN-01",
        scenario_id="SCN-100",
        metric_results=[metric],
        findings=[finding]
    )
    run = EvaluationRun(
        run_id="RUN-01",
        scenario_ids=["SCN-100"],
        passed_count=1,
        overall_accuracy=1.0
    )

    assert result.result_id == "RES-01"
    assert len(result.metric_results) == 1
    assert run.run_id == "RUN-01"
    assert run.overall_accuracy == 1.0


def test_regression_result_model():
    reg = RegressionResult(
        regression_id="REG-01",
        run_id="RUN-02",
        baseline_run_id="RUN-01",
        regression_detected=False
    )
    assert reg.regression_id == "REG-01"
    assert reg.regression_detected is False
