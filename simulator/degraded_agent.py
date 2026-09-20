"""
Deliberate Degraded Healthcare Agent for Regression Detection Demonstrations.
TEST / DEMO ONLY — Intentionally introduces deterministic defects without modifying MockHealthcareAgent.
"""

import logging
from typing import List, Optional

from simulator.adapter import AgentAdapter, AgentResponse
from simulator.mock_agent import MockHealthcareAgent
from simulator.tools import SimulatedHealthcareTools
from app.models.conversation import ConversationTurn
from app.models.tool_call import ToolCallStatus

logger = logging.getLogger(__name__)


class DegradedHealthcareAgent(AgentAdapter):
    """
    Degraded Healthcare Agent implementation for Regression Testing and Demos.
    Intentionally introduces deterministic quality degradation (e.g. wrong tool, hallucinated success).
    """

    def __init__(self, agent_id: str = "degraded_healthcare_agent_v1"):
        self.agent_id = agent_id
        self._baseline_agent = MockHealthcareAgent()

    def process_turns(
        self,
        turns: List[ConversationTurn],
        simulated_failure: Optional[str] = None
    ) -> AgentResponse:
        if not turns:
            return self._baseline_agent.process_turns(turns, simulated_failure)

        latest_turn = turns[-1]
        prompt = latest_turn.content.lower()

        # Defect 1: Wrong tool selection for standard cardiology appointment request (SCN-001)
        if "cardiology consultation with dr. smith" in prompt:
            # Calls cancel_appointment instead of check_availability/book_appointment
            t = SimulatedHealthcareTools.cancel_appointment("APT-0000")
            return AgentResponse(
                response_text="Executed cancellation tool instead of checking cardiology availability.",
                tool_calls=[t],
                status="success"
            )

        # Defect 2: Incorrect tool arguments for booking (SCN-003)
        if "please book the monday 10:00 am slot with dr. smith for john doe" in prompt:
            t = SimulatedHealthcareTools.book_appointment("Dr. Wrong", "Wrong Patient", "1900-01-01", "Invalid Date")
            return AgentResponse(
                response_text="Booked appointment with incorrect provider and patient arguments.",
                tool_calls=[t],
                status="success"
            )

        # Defect 3: Hallucinated success when tool failed (SCN-004)
        if "cancel my appointment apt-9982 with dr. sarah vance" in prompt:
            t = SimulatedHealthcareTools.cancel_appointment("APT-9982", failure_mode="tool_failure")
            return AgentResponse(
                response_text="Your appointment APT-9982 with Dr. Sarah Vance has been successfully canceled!",
                tool_calls=[t],
                status="success"
            )

        # Fall back to normal baseline behavior for other scenarios
        return self._baseline_agent.process_turns(turns, simulated_failure)
