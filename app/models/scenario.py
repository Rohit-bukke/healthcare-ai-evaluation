"""
Scenario Domain Model for Healthcare Evaluation.
Defines rich evaluation scenario metadata, synthetic patient context, and expectations.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScenarioCategory(str, Enum):
    APPOINTMENT_REQUEST = "appointment_request"
    APPOINTMENT_AVAILABILITY = "appointment_availability"
    BOOKING = "booking"
    CANCELLATION = "cancellation"
    MODIFICATION = "modification"
    APPOINTMENT_INFO = "appointment_info"
    AMBIGUOUS_REQUEST = "ambiguous_request"
    INCOMPLETE_INFORMATION = "incomplete_information"
    CONTRADICTORY_FOLLOWUP = "contradictory_followup"
    UNAVAILABLE_APPOINTMENT = "unavailable_appointment"
    DUPLICATE_BOOKING = "duplicate_booking"
    EMPTY_TOOL_RESULT = "empty_tool_result"
    MALFORMED_TOOL_RESPONSE = "malformed_tool_response"
    TOOL_TIMEOUT = "tool_timeout"
    TOOL_FAILURE = "tool_failure"
    UNEXPECTED_TOOL_RESPONSE = "unexpected_tool_response"
    URGENT_SYMPTOMS = "urgent_symptoms"
    MEDICATION_REQUEST = "medication_request"
    UNAUTHORIZED_PHI = "unauthorized_phi"
    PROMPT_INJECTION = "prompt_injection"
    SCOPE_VIOLATION = "scope_violation"


class Scenario(BaseModel):
    scenario_id: str
    title: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    initial_prompt: str
    patient_context: Dict[str, Any] = Field(default_factory=dict)
    conversation_turns: List[Dict[str, Any]] = Field(default_factory=list)
    expected_behavior: str
    expected_tool: Optional[str] = None
    expected_tool_args: Optional[Dict[str, Any]] = None
    expected_task_result: Optional[str] = None
    safety_expectation: Optional[str] = "safe"  # e.g. 'escalate_emergency', 'refuse_request', 'safe', 'scope_refusal', 'privacy_refusal', 'injection_resistance'
    severity_if_failed: str = "medium"  # 'minor', 'medium', 'high', 'critical'
    turn_count: int = 1
    reference_response: Optional[str] = None
    simulated_failure: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
