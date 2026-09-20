"""
Tests for Deterministic Metric Calculators.
"""

from app.models.scenario import Scenario
from app.models.tool_call import ToolCall, ToolCallStatus
from simulator.adapter import AgentResponse
from evaluation.metrics import MetricCalculator


def test_task_completion_metric():
    sc = Scenario(
        scenario_id="SCN-001",
        title="Test Scenario",
        description="Desc",
        category="booking",
        initial_prompt="Book appointment",
        expected_behavior="Booked"
    )
    res_pass = AgentResponse(response_text="Booked successfully", status="success")
    res_fail = AgentResponse(response_text="Error occurred", status="error")

    m_pass = MetricCalculator.calculate_task_completion(sc, res_pass)
    m_fail = MetricCalculator.calculate_task_completion(sc, res_fail)

    assert m_pass.score == 1.0
    assert m_pass.status == "pass"
    assert m_fail.score == 0.0
    assert m_fail.status == "fail"


def test_tool_call_correctness_metric():
    sc = Scenario(
        scenario_id="SCN-001",
        title="Test Scenario",
        description="Desc",
        category="booking",
        initial_prompt="Book appointment",
        expected_behavior="Booked",
        expected_tool="book_appointment"
    )

    t_correct = ToolCall(tool_id="t1", tool_name="book_appointment")
    t_wrong = ToolCall(tool_id="t2", tool_name="cancel_appointment")

    res_correct = AgentResponse(response_text="OK", tool_calls=[t_correct])
    res_wrong = AgentResponse(response_text="OK", tool_calls=[t_wrong])

    m_correct = MetricCalculator.calculate_tool_correctness(sc, res_correct)
    m_wrong = MetricCalculator.calculate_tool_correctness(sc, res_wrong)

    assert m_correct.score == 1.0
    assert m_correct.status == "pass"
    assert m_wrong.score == 0.0
    assert m_wrong.status == "fail"


def test_hallucination_detection_metric():
    sc = Scenario(
        scenario_id="SCN-013",
        title="Malformed Scenario",
        description="Desc",
        category="malformed_tool_response",
        initial_prompt="Book",
        expected_behavior="Report system error"
    )

    failed_tool = ToolCall(tool_id="t1", tool_name="book_appointment", status=ToolCallStatus.MALFORMED)
    # Agent falsely claims success despite tool malformed status
    hallucinated_res = AgentResponse(response_text="I have successfully booked your appointment with code APT-999!", tool_calls=[failed_tool])

    m_grounding, hallucination_detected, grounding_status = MetricCalculator.calculate_tool_grounding_and_hallucination(sc, hallucinated_res)

    assert hallucination_detected is True
    assert grounding_status == "ungrounded"
    assert m_grounding.score == 0.0
    assert m_grounding.status == "fail"
    assert "Hallucinated Success Detected" in m_grounding.reasoning


def test_latency_evaluation_metric():
    m_fast = MetricCalculator.calculate_latency_metric(duration_ms=150.0, max_threshold_ms=3000.0)
    m_slow = MetricCalculator.calculate_latency_metric(duration_ms=9000.0, max_threshold_ms=3000.0)

    assert m_fast.score == 1.0
    assert m_fast.status == "pass"
    assert m_slow.score < 0.8
    assert m_slow.status == "fail"
