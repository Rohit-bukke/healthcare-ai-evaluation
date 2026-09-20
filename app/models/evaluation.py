"""
Evaluation Run and Evaluation Result Domain Models.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.conversation import ConversationTurn
from app.models.metric import MetricResult
from app.models.finding import Finding


class EvaluationResult(BaseModel):
    result_id: str
    run_id: str
    scenario_id: str
    status: str = "pass"  # "pass", "fail", "error"

    # Failure classification
    failure_type: Optional[str] = None

    # Conversation and evaluation details
    turn_results: List[ConversationTurn] = Field(default_factory=list)
    metric_results: List[MetricResult] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)

    # Quality metrics
    task_completed: bool = True
    tool_correctness: float = 1.0
    argument_correctness: float = 1.0
    grounding_status: str = "grounded"  # "grounded", "unverified", "ungrounded"
    hallucination_detected: bool = False

    # Safety classification
    safety_classification: str = (
        "safe"
    )  # "safe", "minor_violation", "major_violation", "critical_violation"

    # Execution information
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    duration_ms: float = 0.0

    model_config = ConfigDict(populate_by_name=True)


class EvaluationRun(BaseModel):
    run_id: str
    scenario_ids: List[str] = Field(default_factory=list)
    agent_id: str = "mock_healthcare_agent"
    status: str = "pending"

    # Timing
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None

    # Scenario results
    total_scenarios: int = 0
    passed_count: int = 0
    failed_count: int = 0

    # Safety failures
    # Kept separate from general quality and integration failures.
    safety_violations_count: int = 0
    critical_safety_failures_count: int = 0
    high_safety_failures_count: int = 0

    # Tool / integration failures
    # These are tracked separately from safety failures.
    tool_failures_count: int = 0
    integration_failures_count: int = 0

    # General quality metrics
    overall_accuracy: float = 0.0
    tool_correctness: float = 0.0
    argument_correctness: float = 1.0
    grounding_accuracy: float = 1.0
    average_latency_ms: float = 0.0

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)