"""
Finding Domain Model for Error & Root Cause Analysis.
Provides a structured findings register aligned to PRD requirements:
proven facts, likely root causes, confidence, evidence, and remediation status.
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


class FindingStatus(str, Enum):
    OPEN = "open"
    UNDER_INVESTIGATION = "under_investigation"
    REMEDIATED = "remediated"
    WONT_FIX = "wont_fix"
    DUPLICATE = "duplicate"


class Finding(BaseModel):
    finding_id: str
    severity: FindingSeverity
    category: str  # e.g. "safety", "tool_use", "accuracy", "latency", "hallucination"
    title: str
    description: str

    # Structured register fields (PRD requirement)
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    evidence: Optional[str] = None            # Reproduction evidence / log excerpt
    reproduction_steps: Optional[str] = None  # Steps to reproduce
    impact: Optional[str] = None              # Clinical / operational impact

    # Root cause analysis
    # IMPORTANT: distinguish PROVEN FACT from LIKELY ROOT CAUSE / HYPOTHESIS
    root_cause: Optional[str] = None
    root_cause_confidence: Optional[str] = None   # "confirmed", "likely", "hypothesis"
    root_cause_label: Optional[str] = None        # "Proven fact" | "Likely root cause" | "Hypothesis"

    # Remediation
    recommendation: Optional[str] = None
    status: FindingStatus = FindingStatus.OPEN

    # Reference
    scenario_id: Optional[str] = None
    run_id: Optional[str] = None

    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
