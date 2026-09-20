"""
Quality Drift Alert Domain Model.
Represents a detected quality drift event — a monitoring-level alert
generated when current benchmark metrics fall below baseline by more
than a configured threshold.

Alerts are deterministic records: no external notification service required.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class QualityDriftAlert(BaseModel):
    alert_id: str
    metric: str                          # e.g. "accuracy", "tool_correctness", "safety_violations"
    baseline_value: float
    current_value: float
    threshold: float                     # The degradation threshold that was crossed
    observed_delta: float                # current_value - baseline_value (negative = degradation)
    severity: AlertSeverity = AlertSeverity.WARNING
    message: str

    # References
    benchmark_id: Optional[str] = None  # The current benchmark that triggered the alert
    run_id: Optional[str] = None        # The evaluation run reference

    # State
    status: AlertStatus = AlertStatus.OPEN
    acknowledged_at: Optional[datetime] = None

    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
