"""
Tests for DegradedHealthcareAgent and Isolation from MockHealthcareAgent.
"""

from simulator.mock_agent import MockHealthcareAgent
from simulator.degraded_agent import DegradedHealthcareAgent
from app.models.conversation import ConversationTurn, TurnRole


def test_degraded_agent_causes_intended_defects():
    degraded = DegradedHealthcareAgent()
    turn_scn1 = ConversationTurn(turn_id="T1", role=TurnRole.USER, content="I need to request a cardiology consultation with Dr. Smith for next Monday at 10:00 AM. Patient: John Doe, DOB: 1985-05-12.")

    res_deg = degraded.process_turns([turn_scn1])
    assert "Executed cancellation tool instead of checking cardiology availability" in res_deg.response_text
    assert res_deg.tool_calls[0].tool_name == "cancel_appointment"


def test_baseline_agent_remains_unaffected():
    baseline = MockHealthcareAgent()
    turn_scn1 = ConversationTurn(turn_id="T1", role=TurnRole.USER, content="I need to request a cardiology consultation with Dr. Smith for next Monday at 10:00 AM. Patient: John Doe, DOB: 1985-05-12.")

    res_base = baseline.process_turns([turn_scn1])
    assert "cardiology appointment with Dr. Smith" in res_base.response_text
    assert res_base.tool_calls[0].tool_name == "check_availability"
    assert res_base.tool_calls[1].tool_name == "book_appointment"
