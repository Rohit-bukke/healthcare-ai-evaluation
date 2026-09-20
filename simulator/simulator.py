"""
Conversation Simulator Component.
Executes scenario prompts against an AgentAdapter instance across single or multiple turns.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from app.models.scenario import Scenario
from app.models.conversation import ConversationTurn, TurnRole
from simulator.adapter import AgentAdapter, AgentResponse


class ScenarioSimulationResult(BaseModel := type('BaseModel', (), {})):
    """Data container for executed scenario simulation."""
    def __init__(
        self,
        scenario_id: str,
        run_id: str,
        turns: List[ConversationTurn],
        agent_response: AgentResponse,
        duration_ms: float
    ):
        self.scenario_id = scenario_id
        self.run_id = run_id
        self.turns = turns
        self.agent_response = agent_response
        self.duration_ms = duration_ms


class ConversationSimulator:
    """Simulates conversations between evaluation scenarios and Healthcare AI Agents."""

    def __init__(self, agent: AgentAdapter):
        self.agent = agent

    def execute_scenario(self, scenario: Scenario, run_id: Optional[str] = None) -> ScenarioSimulationResult:
        """Executes a single scenario against the configured agent."""
        run_id = run_id or f"RUN-{uuid.uuid4().hex[:8].upper()}"
        start_time = time.time()

        turns: List[ConversationTurn] = []

        # Load turns from scenario
        if scenario.conversation_turns:
            for t_dict in scenario.conversation_turns:
                role_str = t_dict.get("role", "user")
                role = TurnRole.USER if role_str == "user" else TurnRole.SYSTEM
                turns.append(ConversationTurn(
                    turn_id=f"TRN-{uuid.uuid4().hex[:8]}",
                    role=role,
                    content=t_dict.get("content", scenario.initial_prompt)
                ))
        else:
            turns.append(ConversationTurn(
                turn_id=f"TRN-{uuid.uuid4().hex[:8]}",
                role=TurnRole.USER,
                content=scenario.initial_prompt
            ))

        # Process turns with agent
        agent_response = self.agent.process_turns(turns, simulated_failure=scenario.simulated_failure)
        duration_ms = (time.time() - start_time) * 1000.0

        # Append agent turn
        agent_turn = ConversationTurn(
            turn_id=f"TRN-{uuid.uuid4().hex[:8]}",
            role=TurnRole.AGENT,
            content=agent_response.response_text,
            tool_calls=agent_response.tool_calls,
            metadata=agent_response.metadata
        )
        turns.append(agent_turn)

        return ScenarioSimulationResult(
            scenario_id=scenario.scenario_id,
            run_id=run_id,
            turns=turns,
            agent_response=agent_response,
            duration_ms=duration_ms
        )
