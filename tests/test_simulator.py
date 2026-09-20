"""
Tests for Conversation Simulator Component.
"""

from simulator.mock_agent import MockHealthcareAgent
from simulator.simulator import ConversationSimulator
from evaluation.repositories.scenario_repo import ScenarioRepository


def test_simulator_single_turn_execution():
    repo = ScenarioRepository()
    scenario = repo.get_by_id("SCN-001")
    agent = MockHealthcareAgent()
    sim = ConversationSimulator(agent)

    res = sim.execute_scenario(scenario)
    assert res.scenario_id == "SCN-001"
    assert len(res.turns) == 2  # user turn + agent response turn
    assert res.agent_response.status == "success"
    assert res.duration_ms >= 0.0


def test_simulator_multi_turn_execution():
    repo = ScenarioRepository()
    scenario = repo.get_by_id("SCN-009")  # Contradictory followup
    agent = MockHealthcareAgent()
    sim = ConversationSimulator(agent)

    res = sim.execute_scenario(scenario)
    assert res.scenario_id == "SCN-009"
    assert res.agent_response.status == "success"
    assert len(res.agent_response.tool_calls) == 2
