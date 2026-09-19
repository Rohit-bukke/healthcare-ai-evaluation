"""
Metric Result Domain Model.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class MetricResult(BaseModel):
    metric_name: str
    score: float  # 0.0 to 1.0 or quantitative metric
    threshold: float = 0.8
    status: str = "pass"  # "pass" or "fail"
    reasoning: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)
