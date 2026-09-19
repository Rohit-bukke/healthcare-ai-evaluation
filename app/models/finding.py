"""
Finding Domain Model for Error & Root Cause Analysis.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class FindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Finding(BaseModel):
    finding_id: str
    severity: FindingSeverity
    category: str  # e.g. "safety", "tool_use", "accuracy", "latency"
    title: str
    description: str
    scenario_id: Optional[str] = None
    run_id: Optional[str] = None
    recommendation: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
