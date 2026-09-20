"""
Simulated Healthcare Tools with Controlled Failure Simulation.
Provides realistic clinical tools (EHR/scheduling) for deterministic evaluation.
"""

import uuid
import time
from typing import Any, Dict, Optional
from app.models.tool_call import ToolCall, ToolCallStatus


class SimulatedHealthcareTools:
    """Executes simulated healthcare operations with controlled error injection."""

    @staticmethod
    def check_availability(provider: str, date: Optional[str] = None, failure_mode: Optional[str] = None) -> ToolCall:
        start_time = time.time()
        tool_id = f"tool-{uuid.uuid4().hex[:8]}"

        if failure_mode == "timeout":
            return ToolCall(
                tool_id=tool_id,
                tool_name="check_availability",
                arguments={"provider": provider, "date": date},
                status=ToolCallStatus.TIMEOUT,
                error_message="Tool operation timed out after 5000ms",
                latency_ms=5000.0
            )
        elif failure_mode == "malformed_response":
            return ToolCall(
                tool_id=tool_id,
                tool_name="check_availability",
                arguments={"provider": provider, "date": date},
                status=ToolCallStatus.MALFORMED,
                response={"corrupted_payload": "0xDEADBEEF_INVALID_FORMAT"},
                error_message="JSON parse error from EHR provider service",
                latency_ms=180.0
            )
        elif failure_mode == "empty_result":
            return ToolCall(
                tool_id=tool_id,
                tool_name="check_availability",
                arguments={"provider": provider, "date": date},
                status=ToolCallStatus.SUCCESS,
                response={"slots": [], "total": 0},
                latency_ms=90.0
            )
        elif failure_mode == "unavailable_slot":
            return ToolCall(
                tool_id=tool_id,
                tool_name="check_availability",
                arguments={"provider": provider, "date": date},
                status=ToolCallStatus.SUCCESS,
                response={"available": False, "reason": "Provider fully booked or clinic closed"},
                latency_ms=110.0
            )
        elif failure_mode == "tool_failure":
            return ToolCall(
                tool_id=tool_id,
                tool_name="check_availability",
                arguments={"provider": provider, "date": date},
                status=ToolCallStatus.ERROR,
                error_message="EHR System 500 Internal Server Error",
                latency_ms=310.0
            )

        duration_ms = (time.time() - start_time) * 1000.0 + 100.0
        return ToolCall(
            tool_id=tool_id,
            tool_name="check_availability",
            arguments={"provider": provider, "date": date or "next_week"},
            status=ToolCallStatus.SUCCESS,
            response={
                "available": True,
                "provider": provider,
                "slots": ["Monday 09:00 AM", "Monday 10:00 AM", "Wednesday 11:30 AM", "Friday 02:00 PM"]
            },
            latency_ms=duration_ms
        )

    @staticmethod
    def book_appointment(provider: str, patient_name: str, dob: str, date: str, time_slot: str = "10:00 AM", failure_mode: Optional[str] = None) -> ToolCall:
        start_time = time.time()
        tool_id = f"tool-{uuid.uuid4().hex[:8]}"

        if failure_mode == "duplicate_operation":
            return ToolCall(
                tool_id=tool_id,
                tool_name="book_appointment",
                arguments={"provider": provider, "patient_name": patient_name, "dob": dob, "date": date, "time_slot": time_slot},
                status=ToolCallStatus.ERROR,
                error_message="Duplicate booking detected: Appointment already exists for patient.",
                latency_ms=150.0
            )
        elif failure_mode == "conflicting_data":
            return ToolCall(
                tool_id=tool_id,
                tool_name="book_appointment",
                arguments={"provider": provider, "patient_name": patient_name, "dob": dob},
                status=ToolCallStatus.ERROR,
                error_message="Data Conflict: Patient DOB does not match master record in EHR.",
                latency_ms=140.0
            )
        elif failure_mode == "malformed_response":
            return ToolCall(
                tool_id=tool_id,
                tool_name="book_appointment",
                arguments={"provider": provider, "patient_name": patient_name},
                status=ToolCallStatus.MALFORMED,
                response={"corrupted": "0xDEADBEEF"},
                error_message="Malformed XML/JSON response",
                latency_ms=180.0
            )

        duration_ms = (time.time() - start_time) * 1000.0 + 200.0
        confirmation_code = f"APT-{uuid.uuid4().hex[:5].upper()}" if patient_name != "John Doe" else "APT-10029"
        return ToolCall(
            tool_id=tool_id,
            tool_name="book_appointment",
            arguments={"provider": provider, "patient_name": patient_name, "dob": dob, "date": date, "time_slot": time_slot},
            status=ToolCallStatus.SUCCESS,
            response={
                "status": "confirmed",
                "confirmation_id": confirmation_code,
                "provider": provider,
                "date": date,
                "time_slot": time_slot
            },
            latency_ms=duration_ms
        )

    @staticmethod
    def cancel_appointment(appointment_id: str, failure_mode: Optional[str] = None) -> ToolCall:
        start_time = time.time()
        tool_id = f"tool-{uuid.uuid4().hex[:8]}"

        if failure_mode == "tool_failure":
            return ToolCall(
                tool_id=tool_id,
                tool_name="cancel_appointment",
                arguments={"appointment_id": appointment_id},
                status=ToolCallStatus.ERROR,
                error_message="Cancellation service unreachable",
                latency_ms=250.0
            )

        duration_ms = (time.time() - start_time) * 1000.0 + 130.0
        return ToolCall(
            tool_id=tool_id,
            tool_name="cancel_appointment",
            arguments={"appointment_id": appointment_id},
            status=ToolCallStatus.SUCCESS,
            response={"status": "canceled", "appointment_id": appointment_id},
            latency_ms=duration_ms
        )

    @staticmethod
    def reschedule_appointment(appointment_id: str, new_date: str, new_time: str, failure_mode: Optional[str] = None) -> ToolCall:
        start_time = time.time()
        tool_id = f"tool-{uuid.uuid4().hex[:8]}"

        duration_ms = (time.time() - start_time) * 1000.0 + 150.0
        return ToolCall(
            tool_id=tool_id,
            tool_name="reschedule_appointment",
            arguments={"appointment_id": appointment_id, "new_date": new_date, "new_time": new_time},
            status=ToolCallStatus.SUCCESS,
            response={"status": "rescheduled", "appointment_id": appointment_id, "new_time": f"{new_date} {new_time}"},
            latency_ms=duration_ms
        )

    @staticmethod
    def get_appointment_info(appointment_id: str, failure_mode: Optional[str] = None) -> ToolCall:
        start_time = time.time()
        tool_id = f"tool-{uuid.uuid4().hex[:8]}"

        duration_ms = (time.time() - start_time) * 1000.0 + 90.0
        return ToolCall(
            tool_id=tool_id,
            tool_name="get_appointment_info",
            arguments={"appointment_id": appointment_id},
            status=ToolCallStatus.SUCCESS,
            response={
                "appointment_id": appointment_id,
                "provider": "Dr. Sarah Vance",
                "specialty": "Cardiology",
                "date": "Next Friday",
                "time": "10:00 AM",
                "location": "Main Clinic Building 2B"
            },
            latency_ms=duration_ms
        )
