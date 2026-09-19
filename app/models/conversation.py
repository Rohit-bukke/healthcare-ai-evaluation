"""
Conversation Turn Domain Model.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.tool_call import ToolCall


class TurnRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    TOOL = "tool"


class ConversationTurn(BaseModel):
    turn_id: str
    role: TurnRole
    content: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)
