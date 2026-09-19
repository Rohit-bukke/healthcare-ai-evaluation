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
    turn_results: List[ConversationTurn] = Field(default_factory=list)
    metric_results: List[MetricResult] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = 0.0

    model_config = ConfigDict(populate_by_name=True)


class EvaluationRun(BaseModel):
    run_id: str
    scenario_ids: List[str] = Field(default_factory=list)
    agent_id: str = "mock_healthcare_agent"
    status: str = "pending"  # "running", "completed", "failed"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    total_scenarios: int = 0
    passed_count: int = 0
    failed_count: int = 0
    overall_accuracy: float = 0.0
    tool_correctness: float = 0.0
    average_latency_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)
