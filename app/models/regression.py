"""
Regression Result Domain Model.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RegressionResult(BaseModel):
    regression_id: str
    baseline_benchmark_id: str
    current_benchmark_id: str
    status: str = "no_regression"  # "no_regression" or "regression_detected"
    regressions_detected: bool = False
    accuracy_delta: float = 0.0
    tool_correctness_delta: float = 0.0
    argument_correctness_delta: float = 0.0
    grounding_accuracy_delta: float = 0.0
    new_failures: List[str] = Field(default_factory=list)
    recovered_failures: List[str] = Field(default_factory=list)
    new_safety_violations: int = 0
    new_tool_failures: int = 0
    new_integration_failures: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
