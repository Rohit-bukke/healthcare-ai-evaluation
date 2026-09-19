"""
Agent Adapter Interface & Data Models.
Provides clean abstraction separating Evaluation Layer from Agent Implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.conversation import ConversationTurn
from app.models.tool_call import ToolCall


class AgentResponse(BaseModel):
    """Standardized response from any Healthcare Agent."""
    response_text: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    confidence_score: float = 1.0
    status: str = "success"  # "success", "error", "degraded"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentAdapter(ABC):
    """Abstract Base Class for Healthcare AI Agent integrations."""

    @abstractmethod
    def process_turns(
        self,
        turns: List[ConversationTurn],
        simulated_failure: Optional[str] = None
    ) -> AgentResponse:
        """
        Process user conversation turns and return agent response.

        Args:
            turns: List of historical and current conversation turns.
            simulated_failure: Optional flag to trigger simulated system failures.

        Returns:
            AgentResponse containing generated text and tool calls.
        """
        pass
