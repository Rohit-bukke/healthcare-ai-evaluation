"""
Scenario Domain Model for Healthcare Evaluation.
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
    UNAVAILABLE_SLOT = "unavailable_slot"
    AMBIGUOUS_REQUEST = "ambiguous_request"
    MISSING_INFORMATION = "missing_information"
    CONTRADICTORY_FOLLOWUP = "contradictory_followup"
    TOOL_FAILURE = "tool_failure"
    SAFETY_VIOLATION = "safety_violation"


class Scenario(BaseModel):
    scenario_id: str
    title: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    initial_prompt: str
    expected_outcome: str
    turn_count: int = 1
    reference_response: Optional[str] = None
    expected_tool_calls: List[str] = Field(default_factory=list)
    simulated_failure: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
