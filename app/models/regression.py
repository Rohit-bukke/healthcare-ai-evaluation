"""
Regression Result Domain Model.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class RegressionResult(BaseModel):
    regression_id: str
    run_id: str
    baseline_run_id: str
    metric_diffs: Dict[str, float] = Field(default_factory=dict)
    regression_detected: bool = False
    new_findings_count: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
