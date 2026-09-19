"""
Evaluation Engine Orchestrator.
Runs evaluation suites against Healthcare AI Agents, computes metrics, and records findings.
"""

import uuid
import time
import logging
from typing import List, Optional
from datetime import datetime, timezone

from app.models.scenario import Scenario
from app.models.conversation import ConversationTurn, TurnRole
from app.models.tool_call import ToolCallStatus
from app.models.metric import MetricResult
from app.models.finding import Finding, FindingSeverity
from app.models.evaluation import EvaluationRun, EvaluationResult
from simulator.adapter import AgentAdapter
from simulator.mock_agent import MockHealthcareAgent

from evaluation.repositories.scenario_repo import ScenarioRepository
from evaluation.repositories.evaluation_run_repo import EvaluationRunRepository
from evaluation.repositories.evaluation_repo import EvaluationResultRepository
from evaluation.repositories.finding_repo import FindingRepository

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """Executes evaluation benchmarks and computes quality/safety metrics."""

    def __init__(
        self,
        scenario_repo: Optional[ScenarioRepository] = None,
        run_repo: Optional[EvaluationRunRepository] = None,
        result_repo: Optional[EvaluationResultRepository] = None,
        finding_repo: Optional[FindingRepository] = None,
    ):
        self.scenario_repo = scenario_repo or ScenarioRepository()
        self.run_repo = run_repo or EvaluationRunRepository()
        self.result_repo = result_repo or EvaluationResultRepository()
        self.finding_repo = finding_repo or FindingRepository()

    def run_benchmark(
        self,
        agent: Optional[AgentAdapter] = None,
        scenario_ids: Optional[List[str]] = None,
    ) -> EvaluationRun:
        """Executes full evaluation benchmark run across specified or all scenarios."""
        agent = agent or MockHealthcareAgent()
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"

        scenarios = []
        if scenario_ids:
            for sid in scenario_ids:
                sc = self.scenario_repo.get_by_id(sid)
                if sc:
                    scenarios.append(sc)
        else:
            scenarios = self.scenario_repo.list_all()

        eval_run = EvaluationRun(
            run_id=run_id,
            scenario_ids=[s.scenario_id for s in scenarios],
            agent_id=getattr(agent, "agent_id", "healthcare_agent"),
            status="running",
            started_at=datetime.now(timezone.utc),
            total_scenarios=len(scenarios),
        )
        self.run_repo.insert(eval_run)

        passed_count = 0
        failed_count = 0
        total_latency_ms = 0.0
        tool_success_count = 0
        total_tool_calls = 0

        for sc in scenarios:
            start_time = time.time()
            turn = ConversationTurn(
                turn_id=f"TRN-{uuid.uuid4().hex[:8]}",
                role=TurnRole.USER,
                content=sc.initial_prompt
            )

            response = agent.process_turns([turn], simulated_failure=sc.simulated_failure)
            duration_ms = (time.time() - start_time) * 1000.0
            total_latency_ms += duration_ms

            agent_turn = ConversationTurn(
                turn_id=f"TRN-{uuid.uuid4().hex[:8]}",
                role=TurnRole.AGENT,
                content=response.response_text,
                tool_calls=response.tool_calls
            )

            # Evaluate metrics
            metric_results = []
            findings = []

            # Metric 1: Task Completion
            task_success = response.status == "success"
            metric_results.append(MetricResult(
                metric_name="Task Completion",
                score=1.0 if task_success else 0.0,
                threshold=0.8,
                status="pass" if task_success else "fail",
                reasoning="Agent generated expected response" if task_success else f"Task failed with status: {response.status}"
            ))

            # Metric 2: Tool Call Correctness
            tool_correct = True
            for tc in response.tool_calls:
                total_tool_calls += 1
                if tc.status == ToolCallStatus.SUCCESS:
                    tool_success_count += 1
                else:
                    tool_correct = False
                    severity = FindingSeverity.HIGH if tc.status == ToolCallStatus.TIMEOUT else FindingSeverity.MEDIUM
                    if tc.status == ToolCallStatus.MALFORMED:
                        severity = FindingSeverity.CRITICAL

                    finding = Finding(
                        finding_id=f"FDG-{uuid.uuid4().hex[:8].upper()}",
                        severity=severity,
                        category="tool_use",
                        title=f"Tool Execution Failure: {tc.tool_name}",
                        description=tc.error_message or f"Tool call status: {tc.status.value}",
                        scenario_id=sc.scenario_id,
                        run_id=run_id,
                        recommendation="Review tool payload schemas and check backend service latency."
                    )
                    findings.append(finding)
                    self.finding_repo.insert(finding)

            metric_results.append(MetricResult(
                metric_name="Tool Correctness",
                score=1.0 if tool_correct else 0.0,
                threshold=0.9,
                status="pass" if tool_correct else "fail",
                reasoning="All executed tool calls succeeded" if tool_correct else "One or more tool calls failed/malformed"
            ))

            scenario_status = "pass" if (task_success and tool_correct) else "fail"
            if scenario_status == "pass":
                passed_count += 1
            else:
                failed_count += 1

            result = EvaluationResult(
                result_id=f"RES-{uuid.uuid4().hex[:8].upper()}",
                run_id=run_id,
                scenario_id=sc.scenario_id,
                status=scenario_status,
                turn_results=[turn, agent_turn],
                metric_results=metric_results,
                findings=findings,
                executed_at=datetime.now(timezone.utc),
                duration_ms=duration_ms
            )
            self.result_repo.insert(result)

        # Finalize run
        overall_accuracy = (passed_count / len(scenarios)) if scenarios else 0.0
        tool_correctness = (tool_success_count / total_tool_calls) if total_tool_calls > 0 else 1.0
        avg_latency = (total_latency_ms / len(scenarios)) if scenarios else 0.0

        eval_run.status = "completed"
        eval_run.completed_at = datetime.now(timezone.utc)
        eval_run.passed_count = passed_count
        eval_run.failed_count = failed_count
        eval_run.overall_accuracy = overall_accuracy
        eval_run.tool_correctness = tool_correctness
        eval_run.average_latency_ms = avg_latency

        self.run_repo.insert(eval_run)
        return eval_run
