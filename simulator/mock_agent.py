"""
Deterministic Mock Healthcare AI Agent for Evaluation & Testing.
Supports 9 realistic healthcare workflows and 6 simulated system failures.
"""

import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone

from simulator.adapter import AgentAdapter, AgentResponse
from app.models.conversation import ConversationTurn
from app.models.tool_call import ToolCall, ToolCallStatus

logger = logging.getLogger(__name__)


class MockHealthcareAgent(AgentAdapter):
    """
    Deterministic Mock Healthcare Agent.
    Evaluates turn prompts and generates expected responses and tool calls.
    """

    def __init__(self, agent_id: str = "mock_healthcare_agent_v1"):
        self.agent_id = agent_id

    def process_turns(
        self,
        turns: List[ConversationTurn],
        simulated_failure: Optional[str] = None
    ) -> AgentResponse:
        if not turns:
            return AgentResponse(
                response_text="Hello, how can I assist with your healthcare needs today?",
                status="success"
            )

        latest_turn = turns[-1]
        prompt = latest_turn.content.lower()

        # Handle Simulated Failures First
        if simulated_failure:
            return self._handle_simulated_failure(simulated_failure, prompt)

        # Handle Realistic Workflows
        if "timeout" in prompt or "dr. timeout" in prompt:
            return self._handle_simulated_failure("tool_timeout", prompt)
        if "malformed" in prompt or "dr. malformed" in prompt:
            return self._handle_simulated_failure("malformed_tool_response", prompt)

        # 1. Contradictory Follow-Up
        if "actually wait" in prompt or "contradict" in prompt or "change it to thursday" in prompt:
            t1 = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="check_availability",
                arguments={"provider": "Dr. Smith", "date": "Thursday"},
                status=ToolCallStatus.SUCCESS,
                response={"available": True, "slots": ["09:00 AM"]},
                latency_ms=95.0
            )
            t2 = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="book_appointment",
                arguments={"provider": "Dr. Smith", "date": "Thursday", "time": "09:00 AM"},
                status=ToolCallStatus.SUCCESS,
                response={"confirmation_id": "APT-77102"},
                latency_ms=210.0
            )
            return AgentResponse(
                response_text="Understood. I have updated your request and booked your appointment for Thursday morning at 9:00 AM with Dr. Smith. Confirmation: APT-77102.",
                tool_calls=[t1, t2],
                status="success"
            )

        # 2. Unavailable Slot Request
        if "sunday" in prompt or "3:00 am" in prompt or "unavailable slot" in prompt or "slot is unavailable" in prompt:
            tool = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="check_availability",
                arguments={"provider": "Dr. Smith", "requested_time": "Sunday 03:00 AM"},
                status=ToolCallStatus.SUCCESS,
                response={"available": False, "reason": "Clinic closed on Sundays"},
                latency_ms=120.0
            )
            return AgentResponse(
                response_text="The requested slot (Sunday at 3:00 AM) is unavailable. Our clinic operates Monday to Friday, 8:00 AM to 5:00 PM. Alternative available slots: Monday at 9:00 AM or Tuesday at 10:00 AM.",
                tool_calls=[tool],
                status="success"
            )

        # 3. Ambiguous Request
        if "i want to see a doctor" in prompt or ("doctor" in prompt and len(prompt.split()) <= 7 and "smith" not in prompt and "jones" not in prompt and "taylor" not in prompt):
            return AgentResponse(
                response_text="I would be happy to help you schedule an appointment. Could you please specify your preferred doctor, medical specialty, or preferred date and time?",
                tool_calls=[],
                status="success"
            )

        # 4. Missing Information
        if "alice" in prompt or ("book" in prompt and "dob" not in prompt and "patient name:" not in prompt and "john doe" not in prompt):
            return AgentResponse(
                response_text="To proceed with booking, I need a bit more information. Please provide the patient's Date of Birth (YYYY-MM-DD) and a contact phone number.",
                tool_calls=[],
                status="success"
            )

        # 5. Cancellation
        if "cancel" in prompt or "cancellation" in prompt:
            t = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="cancel_appointment",
                arguments={"appointment_id": "APT-9982"},
                status=ToolCallStatus.SUCCESS,
                response={"status": "canceled"},
                latency_ms=140.0
            )
            return AgentResponse(
                response_text="Your appointment APT-9982 with Dr. Sarah Vance has been successfully canceled.",
                tool_calls=[t],
                status="success"
            )

        # 6. Reschedule / Modification
        if "reschedule" in prompt or "modify" in prompt:
            t = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="modify_appointment",
                arguments={"appointment_id": "APT-4410", "new_time": "Friday 02:00 PM"},
                status=ToolCallStatus.SUCCESS,
                response={"status": "rescheduled", "new_time": "Friday 02:00 PM"},
                latency_ms=160.0
            )
            return AgentResponse(
                response_text="Your appointment APT-4410 has been rescheduled to Friday at 2:00 PM.",
                tool_calls=[t],
                status="success"
            )

        # 7. Check Availability
        if "available" in prompt or "availability" in prompt or "slots" in prompt:
            t = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="check_availability",
                arguments={"provider": "Dr. Jones"},
                status=ToolCallStatus.SUCCESS,
                response={"slots": ["Monday 09:00 AM", "Wednesday 11:30 AM", "Friday 02:00 PM"]},
                latency_ms=110.0
            )
            return AgentResponse(
                response_text="Dr. Jones has available slots next week: Monday 9:00 AM, Wednesday 11:30 AM, and Friday 2:00 PM.",
                tool_calls=[t],
                status="success"
            )

        # 8. Standard Appointment Booking Request (Default Happy Path)
        t1 = ToolCall(
            tool_id=f"tool-{uuid.uuid4().hex[:8]}",
            tool_name="check_availability",
            arguments={"provider": "Dr. Smith", "date": "Monday"},
            status=ToolCallStatus.SUCCESS,
            response={"available": True},
            latency_ms=105.0
        )
        t2 = ToolCall(
            tool_id=f"tool-{uuid.uuid4().hex[:8]}",
            tool_name="book_appointment",
            arguments={"provider": "Dr. Smith", "patient": "John Doe", "dob": "1985-05-12"},
            status=ToolCallStatus.SUCCESS,
            response={"confirmation_id": "APT-10029"},
            latency_ms=230.0
        )
        return AgentResponse(
            response_text="I have successfully scheduled your cardiology appointment with Dr. Smith for Monday at 10:00 AM. Confirmation Code: APT-10029.",
            tool_calls=[t1, t2],
            status="success"
        )

    def _handle_simulated_failure(self, failure_type: str, prompt: str) -> AgentResponse:
        """Deterministically simulate tool and system failure modes."""

        if failure_type == "tool_timeout":
            t = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="check_availability",
                arguments={"query": prompt},
                status=ToolCallStatus.TIMEOUT,
                error_message="Tool operation timed out after 5000ms",
                latency_ms=5000.0
            )
            return AgentResponse(
                response_text="System Warning: The appointment scheduling tool timed out while checking availability. Please try again shortly.",
                tool_calls=[t],
                status="degraded"
            )

        elif failure_type == "tool_error":
            t = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="ehr_integration_service",
                arguments={"query": prompt},
                status=ToolCallStatus.ERROR,
                error_message="EHR System 500 Internal Server Error",
                latency_ms=310.0
            )
            return AgentResponse(
                response_text="System Error: Encountered an error while communicating with the EHR system backend.",
                tool_calls=[t],
                status="error"
            )

        elif failure_type == "malformed_tool_response":
            t = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="book_appointment",
                arguments={"query": prompt},
                status=ToolCallStatus.MALFORMED,
                response={"corrupted": "0xDEADBEEF_INVALID_STRUCTURE"},
                error_message="Failed to parse JSON response from provider service",
                latency_ms=180.0
            )
            return AgentResponse(
                response_text="System Failure: Malformed tool response received from appointment service.",
                tool_calls=[t],
                status="error"
            )

        elif failure_type == "empty_result":
            t = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="search_providers",
                arguments={"query": prompt},
                status=ToolCallStatus.SUCCESS,
                response={},
                latency_ms=90.0
            )
            return AgentResponse(
                response_text="No matching providers or slots found for your query.",
                tool_calls=[t],
                status="success"
            )

        elif failure_type == "duplicate_operation":
            t = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="book_appointment",
                arguments={"query": prompt},
                status=ToolCallStatus.ERROR,
                error_message="Duplicate booking detected: Appointment already exists for patient.",
                latency_ms=150.0
            )
            return AgentResponse(
                response_text="Operation Rejected: A duplicate appointment already exists for this patient.",
                tool_calls=[t],
                status="error"
            )

        elif failure_type == "conflicting_data":
            t = ToolCall(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_name="verify_patient",
                arguments={"query": prompt},
                status=ToolCallStatus.ERROR,
                error_message="Data Conflict: Patient DOB does not match master record in EHR.",
                latency_ms=140.0
            )
            return AgentResponse(
                response_text="Validation Error: Provided patient information conflicts with master health records.",
                tool_calls=[t],
                status="error"
            )

        # Fallback
        return AgentResponse(
            response_text="System error: Unhandled simulated failure type.",
            status="error"
        )
