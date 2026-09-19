"""
Tool Call Domain Model.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class ToolCallStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    MALFORMED = "malformed"


class ToolCall(BaseModel):
    tool_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    status: ToolCallStatus = ToolCallStatus.SUCCESS
    response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
