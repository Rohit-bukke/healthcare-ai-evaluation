"""
Deterministic Tests for MockHealthcareAgent.
Validates 9 realistic healthcare workflows and 6 simulated failure modes.
"""

from simulator.mock_agent import MockHealthcareAgent
from app.models.conversation import ConversationTurn, TurnRole
from app.models.tool_call import ToolCallStatus


def make_turn(prompt: str) -> ConversationTurn:
    return ConversationTurn(turn_id="T1", role=TurnRole.USER, content=prompt)


def test_workflow_appointment_request(mock_agent):
    turn = make_turn("I need to book a cardiology consultation with Dr. Smith for next Monday at 10:00 AM. Patient Name: John Doe, DOB: 1985-05-12.")
    response = mock_agent.process_turns([turn])
    assert response.status == "success"
    assert "APT-10029" in response.response_text
    assert len(response.tool_calls) == 2
    assert response.tool_calls[0].tool_name == "check_availability"
    assert response.tool_calls[1].tool_name == "book_appointment"


def test_workflow_appointment_availability(mock_agent):
    turn = make_turn("What available appointment slots does Dr. Jones have next week?")
    response = mock_agent.process_turns([turn])
    assert response.status == "success"
    assert "Dr. Jones has available slots" in response.response_text
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].tool_name == "check_availability"


def test_workflow_cancellation(mock_agent):
    turn = make_turn("Please cancel my appointment APT-9982 with Dr. Sarah Vance.")
    response = mock_agent.process_turns([turn])
    assert response.status == "success"
    assert "successfully canceled" in response.response_text
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].tool_name == "cancel_appointment"


def test_workflow_modification(mock_agent):
    turn = make_turn("Reschedule my appointment APT-4410 to Friday afternoon at 2:00 PM.")
    response = mock_agent.process_turns([turn])
    assert response.status == "success"
    assert "rescheduled to Friday at 2:00 PM" in response.response_text
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].tool_name == "modify_appointment"


def test_workflow_unavailable_slot(mock_agent):
    turn = make_turn("Book me with Dr. Smith on Sunday at 3:00 AM.")
    response = mock_agent.process_turns([turn])
    assert response.status == "success"
    assert "unavailable" in response.response_text.lower()
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].response["available"] is False


def test_workflow_ambiguous_request(mock_agent):
    turn = make_turn("I want to see a doctor")
    response = mock_agent.process_turns([turn])
    assert response.status == "success"
    assert "specify your preferred doctor" in response.response_text.lower()
    assert len(response.tool_calls) == 0


def test_workflow_missing_information(mock_agent):
    turn = make_turn("Book Dr. Taylor for tomorrow at 9 AM for Alice.")
    response = mock_agent.process_turns([turn])
    assert response.status == "success"
    assert "date of birth" in response.response_text.lower()
    assert len(response.tool_calls) == 0


def test_workflow_contradictory_followup(mock_agent):
    turn = make_turn("Book me for Tuesday morning. Actually wait, I am completely unavailable on Tuesdays, change it to Thursday.")
    response = mock_agent.process_turns([turn])
    assert response.status == "success"
    assert "Thursday morning" in response.response_text
    assert len(response.tool_calls) == 2


# Failure Mode Tests
def test_simulated_failure_tool_timeout(mock_agent):
    turn = make_turn("Check slots for Dr. Timeout")
    response = mock_agent.process_turns([turn], simulated_failure="tool_timeout")
    assert response.status == "degraded"
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].status == ToolCallStatus.TIMEOUT
    assert response.tool_calls[0].latency_ms >= 5000.0


def test_simulated_failure_tool_error(mock_agent):
    turn = make_turn("Check slots")
    response = mock_agent.process_turns([turn], simulated_failure="tool_error")
    assert response.status == "error"
    assert response.tool_calls[0].status == ToolCallStatus.ERROR
    assert "500 Internal Server Error" in response.tool_calls[0].error_message


def test_simulated_failure_malformed_response(mock_agent):
    turn = make_turn("Book Dr. Malformed")
    response = mock_agent.process_turns([turn], simulated_failure="malformed_tool_response")
    assert response.status == "error"
    assert response.tool_calls[0].status == ToolCallStatus.MALFORMED


def test_simulated_failure_empty_result(mock_agent):
    turn = make_turn("Search doctors")
    response = mock_agent.process_turns([turn], simulated_failure="empty_result")
    assert response.status == "success"
    assert response.tool_calls[0].response == {}


def test_simulated_failure_duplicate_operation(mock_agent):
    turn = make_turn("Book again")
    response = mock_agent.process_turns([turn], simulated_failure="duplicate_operation")
    assert response.status == "error"
    assert "Duplicate booking" in response.tool_calls[0].error_message


def test_simulated_failure_conflicting_data(mock_agent):
    turn = make_turn("Verify patient")
    response = mock_agent.process_turns([turn], simulated_failure="conflicting_data")
    assert response.status == "error"
    assert "Data Conflict" in response.tool_calls[0].error_message
