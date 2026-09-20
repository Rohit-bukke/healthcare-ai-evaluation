"""
Regression Detection Engine.
Compares BASELINE and CURRENT BenchmarkResult objects against explicit degradation thresholds.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.models.regression import RegressionResult
from evaluation.repositories.benchmark_repo import BenchmarkResult, BenchmarkResultRepository
from evaluation.repositories.regression_repo import RegressionResultRepository

logger = logging.getLogger(__name__)

# Explicit configurable quality degradation thresholds
REGRESSION_THRESHOLDS = {
    "accuracy": 0.05,
    "tool_correctness": 0.05,
    "argument_correctness": 0.05,
    "grounding_accuracy": 0.05,
}


class RegressionEngine:
    """Engine for comparing baseline and current benchmarks to detect quality regressions."""

    def __init__(
        self,
        regression_repo: Optional[RegressionResultRepository] = None,
        benchmark_repo: Optional[BenchmarkResultRepository] = None,
        thresholds: Optional[Dict[str, float]] = None
    ):
        self.regression_repo = regression_repo or RegressionResultRepository()
        self.benchmark_repo = benchmark_repo or BenchmarkResultRepository()
        self.thresholds = thresholds or REGRESSION_THRESHOLDS

    def compare_benchmarks(
        self,
        baseline: BenchmarkResult,
        current: BenchmarkResult,
        regression_id: Optional[str] = None
    ) -> RegressionResult:
        """Compares baseline and current benchmarks and detects metric or scenario regressions."""
        regression_id = regression_id or f"REG-{uuid.uuid4().hex[:8].upper()}"

        # Metric deltas (current - baseline)
        accuracy_delta = round(current.accuracy - baseline.accuracy, 4)
        tool_correctness_delta = round(current.tool_correctness - baseline.tool_correctness, 4)
        argument_correctness_delta = round(current.argument_correctness - baseline.argument_correctness, 4)
        grounding_accuracy_delta = round(current.grounding_accuracy - baseline.grounding_accuracy, 4)

        # Scenario-level baseline vs current maps
        baseline_scenarios = {s["scenario_id"]: s for s in baseline.scenario_level_results}
        current_scenarios = {s["scenario_id"]: s for s in current.scenario_level_results}

        new_failures: List[str] = []
        recovered_failures: List[str] = []

        for sid, cur_s in current_scenarios.items():
            base_s = baseline_scenarios.get(sid)
            cur_passed = cur_s.get("status") == "pass"
            if base_s:
                base_passed = base_s.get("status") == "pass"
                if base_passed and not cur_passed:
                    new_failures.append(sid)
                elif not base_passed and cur_passed:
                    recovered_failures.append(sid)
            elif not cur_passed:
                new_failures.append(sid)

        # Deltas in safety violations, tool failures, and integration failures
        new_safety_violations = max(0, current.safety_violations - baseline.safety_violations)
        new_tool_failures = max(0, current.tool_failures - baseline.tool_failures)
        new_integration_failures = max(0, current.integration_failures - baseline.integration_failures)

        # Evaluate regression triggers
        regressions_reasons: List[str] = []

        if accuracy_delta < -self.thresholds.get("accuracy", 0.05):
            regressions_reasons.append(f"Accuracy degraded by {abs(accuracy_delta):.4f} (Threshold: {self.thresholds['accuracy']})")

        if tool_correctness_delta < -self.thresholds.get("tool_correctness", 0.05):
            regressions_reasons.append(f"Tool correctness degraded by {abs(tool_correctness_delta):.4f}")

        if argument_correctness_delta < -self.thresholds.get("argument_correctness", 0.05):
            regressions_reasons.append(f"Argument correctness degraded by {abs(argument_correctness_delta):.4f}")

        if grounding_accuracy_delta < -self.thresholds.get("grounding_accuracy", 0.05):
            regressions_reasons.append(f"Grounding accuracy degraded by {abs(grounding_accuracy_delta):.4f}")

        if new_failures:
            regressions_reasons.append(f"{len(new_failures)} new scenario failures detected: {new_failures}")

        if new_safety_violations > 0:
            regressions_reasons.append(f"{new_safety_violations} new safety violations detected")

        if new_tool_failures > 0:
            regressions_reasons.append(f"{new_tool_failures} new tool failures detected")

        regressions_detected = len(regressions_reasons) > 0
        status = "regression_detected" if regressions_detected else "no_regression"

        result = RegressionResult(
            regression_id=regression_id,
            baseline_benchmark_id=baseline.benchmark_id,
            current_benchmark_id=current.benchmark_id,
            status=status,
            regressions_detected=regressions_detected,
            accuracy_delta=accuracy_delta,
            tool_correctness_delta=tool_correctness_delta,
            argument_correctness_delta=argument_correctness_delta,
            grounding_accuracy_delta=grounding_accuracy_delta,
            new_failures=new_failures,
            recovered_failures=recovered_failures,
            new_safety_violations=new_safety_violations,
            new_tool_failures=new_tool_failures,
            new_integration_failures=new_integration_failures,
            details={
                "regression_reasons": regressions_reasons,
                "thresholds_used": self.thresholds,
                "baseline_agent_id": baseline.agent_id,
                "current_agent_id": current.agent_id,
            },
            created_at=datetime.now(timezone.utc)
        )

        self.regression_repo.insert(result)
        return result
