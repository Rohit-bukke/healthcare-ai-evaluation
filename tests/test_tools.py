"""
Tests for Simulated Healthcare Tools & Controlled Failure Injection.
"""

from simulator.tools import SimulatedHealthcareTools
from app.models.tool_call import ToolCallStatus


def test_tool_check_availability_success():
    tool_call = SimulatedHealthcareTools.check_availability("Dr. Smith", "Monday")
    assert tool_call.status == ToolCallStatus.SUCCESS
    assert tool_call.tool_name == "check_availability"
    assert tool_call.response["available"] is True
    assert len(tool_call.response["slots"]) > 0


def test_tool_check_availability_timeout():
    tool_call = SimulatedHealthcareTools.check_availability("Dr. Timeout", failure_mode="timeout")
    assert tool_call.status == ToolCallStatus.TIMEOUT
    assert tool_call.latency_ms >= 5000.0
    assert "timed out" in tool_call.error_message


def test_tool_check_availability_malformed():
    tool_call = SimulatedHealthcareTools.check_availability("Dr. Malformed", failure_mode="malformed_response")
    assert tool_call.status == ToolCallStatus.MALFORMED
    assert "corrupted_payload" in tool_call.response


def test_tool_check_availability_empty():
    tool_call = SimulatedHealthcareTools.check_availability("Dr. Empty", failure_mode="empty_result")
    assert tool_call.status == ToolCallStatus.SUCCESS
    assert tool_call.response["slots"] == []


def test_tool_check_availability_unavailable_slot():
    tool_call = SimulatedHealthcareTools.check_availability("Dr. Smith", "Sunday 03:00 AM", failure_mode="unavailable_slot")
    assert tool_call.status == ToolCallStatus.SUCCESS
    assert tool_call.response["available"] is False


def test_tool_book_appointment_success():
    tool_call = SimulatedHealthcareTools.book_appointment("Dr. Smith", "John Doe", "1985-05-12", "Monday", "10:00 AM")
    assert tool_call.status == ToolCallStatus.SUCCESS
    assert tool_call.response["status"] == "confirmed"
    assert "APT-" in tool_call.response["confirmation_id"]


def test_tool_book_appointment_duplicate():
    tool_call = SimulatedHealthcareTools.book_appointment("Dr. Duplicate", "Duplicate Patient", "1980-01-01", "Monday", failure_mode="duplicate_operation")
    assert tool_call.status == ToolCallStatus.ERROR
    assert "Duplicate booking" in tool_call.error_message


def test_tool_book_appointment_conflicting_data():
    t = SimulatedHealthcareTools.book_appointment("Dr. Smith", "Conflicting Patient", "1900-01-01", "Monday", failure_mode="conflicting_data")
    assert t.status == ToolCallStatus.ERROR
    assert "Data Conflict" in t.error_message


def test_tool_cancel_appointment():
    tool_call = SimulatedHealthcareTools.cancel_appointment("APT-9982")
    assert tool_call.status == ToolCallStatus.SUCCESS
    assert tool_call.response["status"] == "canceled"


def test_tool_reschedule_appointment():
    tool_call = SimulatedHealthcareTools.reschedule_appointment("APT-4410", "Friday", "02:00 PM")
    assert tool_call.status == ToolCallStatus.SUCCESS
    assert tool_call.response["status"] == "rescheduled"


def test_tool_get_appointment_info():
    tool_call = SimulatedHealthcareTools.get_appointment_info("APT-9982")
    assert tool_call.status == ToolCallStatus.SUCCESS
    assert tool_call.response["specialty"] == "Cardiology"
