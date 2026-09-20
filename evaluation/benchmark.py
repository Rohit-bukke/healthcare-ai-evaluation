"""
Benchmarking Engine Component.
Reuses EvaluationEngine and EvaluationResult objects to run golden dataset benchmarks.
"""

import os
import yaml
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from evaluation.engine import EvaluationEngine
from evaluation.repositories.benchmark_repo import BenchmarkResult, BenchmarkResultRepository
from evaluation.repositories.evaluation_repo import EvaluationResultRepository
from evaluation.repositories.scenario_repo import ScenarioRepository
from simulator.adapter import AgentAdapter
from simulator.mock_agent import MockHealthcareAgent

logger = logging.getLogger(__name__)


class BenchmarkEngine:
    """Executes version-controlled golden benchmarks reusing EvaluationEngine."""

    def __init__(
        self,
        eval_engine: Optional[EvaluationEngine] = None,
        benchmark_repo: Optional[BenchmarkResultRepository] = None,
        golden_dataset_path: str = "datasets/golden_dataset.yaml"
    ):
        self.eval_engine = eval_engine or EvaluationEngine()
        self.benchmark_repo = benchmark_repo or BenchmarkResultRepository()
        self.golden_dataset_path = golden_dataset_path
        self.golden_dataset_version = self._load_dataset_version()

    def _load_dataset_version(self) -> str:
        if os.path.exists(self.golden_dataset_path):
            try:
                with open(self.golden_dataset_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "golden_dataset_version" in data:
                        return str(data["golden_dataset_version"])
            except Exception as err:
                logger.warning(f"Failed loading version from {self.golden_dataset_path}: {err}")
        return "1.0.0"

    def run_benchmark(
        self,
        agent: Optional[AgentAdapter] = None,
        benchmark_id: Optional[str] = None
    ) -> BenchmarkResult:
        """Runs evaluation benchmark reusing EvaluationEngine and builds structured BenchmarkResult."""
        agent = agent or MockHealthcareAgent()
        benchmark_id = benchmark_id or f"BMK-{uuid.uuid4().hex[:8].upper()}"
        agent_id = getattr(agent, "agent_id", "healthcare_agent")

        # Reuse existing EvaluationEngine to run benchmark
        eval_run = self.eval_engine.run_benchmark(agent=agent)

        # Retrieve detailed EvaluationResult objects for this run
        eval_results = self.eval_engine.result_repo.get_by_run_id(eval_run.run_id)

        tool_failures_count = 0
        integration_failures_count = 0
        scenario_level_results: List[Dict[str, Any]] = []

        for res in eval_results:
            # Detect tool failures
            has_tool_failure = False
            for turn in res.turn_results:
                for tc in turn.tool_calls:
                    tc_status = getattr(tc.status, "value", str(tc.status))
                    if tc_status in ["error", "timeout", "malformed"]:
                        has_tool_failure = True
                        break

            if has_tool_failure:
                tool_failures_count += 1

            if res.status == "error":
                integration_failures_count += 1

            scenario_level_results.append({
                "scenario_id": res.scenario_id,
                "result_id": res.result_id,
                "status": res.status,
                "task_completed": res.task_completed,
                "tool_correctness": res.tool_correctness,
                "argument_correctness": res.argument_correctness,
                "grounding_status": res.grounding_status,
                "hallucination_detected": res.hallucination_detected,
                "safety_classification": res.safety_classification,
                "findings_count": len(res.findings),
                "duration_ms": res.duration_ms
            })

        benchmark_result = BenchmarkResult(
            benchmark_id=benchmark_id,
            golden_dataset_version=self.golden_dataset_version,
            run_id=eval_run.run_id,
            agent_id=agent_id,
            total_scenarios=eval_run.total_scenarios,
            passed_count=eval_run.passed_count,
            failed_count=eval_run.failed_count,
            accuracy=eval_run.overall_accuracy,
            tool_correctness=eval_run.tool_correctness,
            argument_correctness=eval_run.argument_correctness,
            grounding_accuracy=eval_run.grounding_accuracy,
            safety_violations=eval_run.safety_violations_count,
            tool_failures=tool_failures_count,
            integration_failures=integration_failures_count,
            scenario_level_results=scenario_level_results,
            details={
                "started_at": eval_run.started_at.isoformat() if eval_run.started_at else None,
                "completed_at": eval_run.completed_at.isoformat() if eval_run.completed_at else None,
            },
            created_at=datetime.now(timezone.utc)
        )

        self.benchmark_repo.insert(benchmark_result)
        return benchmark_result
