"""
Quality Drift Detection Service.

Compares recent/current benchmark metrics against a documented baseline
to detect configurable metric degradation. This is a monitoring-level
interpretation of existing benchmark/evaluation results.

Design principles:
- Deterministic: no external services or AI judges required.
- Reuses regression threshold philosophy from RegressionEngine.
- Does NOT replace or duplicate RegressionEngine.
  RegressionEngine → detects regressions between two benchmark runs.
  QualityDriftService → interprets a current benchmark against a fixed baseline
    snapshot and generates persistent QualityDriftAlert records.
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.models.alert import QualityDriftAlert, AlertSeverity, AlertStatus
from evaluation.repositories.alert_repo import AlertRepository
from evaluation.repositories.benchmark_repo import BenchmarkResult

logger = logging.getLogger(__name__)


# Default drift thresholds (configurable at runtime)
DEFAULT_DRIFT_THRESHOLDS: Dict[str, float] = {
    "accuracy": 0.05,
    "tool_correctness": 0.05,
    "argument_correctness": 0.05,
    "grounding_accuracy": 0.05,
}

# Safety and failure counts are monitored in absolute numbers (any increase is flagged)
SAFETY_FAILURE_THRESHOLD = 1   # Any new safety violation triggers WARNING
TOOL_FAILURE_THRESHOLD = 2     # >2 new tool failures triggers WARNING


class DriftCheckResult:
    """
    Container for a complete drift check result.
    Not persisted to MongoDB — it holds the alerts that were generated.
    """

    def __init__(
        self,
        baseline_benchmark_id: str,
        current_benchmark_id: str,
        alerts_generated: List[QualityDriftAlert],
        metrics_compared: Dict[str, Any],
        drift_detected: bool,
    ):
        self.baseline_benchmark_id = baseline_benchmark_id
        self.current_benchmark_id = current_benchmark_id
        self.alerts_generated = alerts_generated
        self.metrics_compared = metrics_compared
        self.drift_detected = drift_detected
        self.checked_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_benchmark_id": self.baseline_benchmark_id,
            "current_benchmark_id": self.current_benchmark_id,
            "drift_detected": self.drift_detected,
            "alerts_generated": len(self.alerts_generated),
            "alert_ids": [a.alert_id for a in self.alerts_generated],
            "metrics_compared": self.metrics_compared,
            "checked_at": self.checked_at.isoformat(),
        }


class QualityDriftService:
    """
    Monitoring-level quality drift detection service.

    Compares a current benchmark result against a baseline benchmark
    snapshot. For each metric that has degraded beyond its threshold,
    generates and persists a QualityDriftAlert.

    Safety violations, tool failures, and integration failures are
    tracked separately and never collapsed into a generic quality score.
    """

    def __init__(
        self,
        alert_repo: Optional[AlertRepository] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ):
        self.alert_repo = alert_repo or AlertRepository()
        self.thresholds = thresholds or DEFAULT_DRIFT_THRESHOLDS

    def check_drift(
        self,
        baseline: BenchmarkResult,
        current: BenchmarkResult,
    ) -> DriftCheckResult:
        """
        Compare current benchmark metrics against baseline.
        Generate and persist QualityDriftAlert records for any detected degradations.

        Returns:
            DriftCheckResult containing all generated alerts and comparison metadata.
        """
        alerts: List[QualityDriftAlert] = []
        metrics_compared: Dict[str, Any] = {}

        # --- Continuous quality metrics ---
        continuous_metrics = [
            ("accuracy", baseline.accuracy, current.accuracy),
            ("tool_correctness", baseline.tool_correctness, current.tool_correctness),
            ("argument_correctness", baseline.argument_correctness, current.argument_correctness),
            ("grounding_accuracy", baseline.grounding_accuracy, current.grounding_accuracy),
        ]

        for metric_name, baseline_val, current_val in continuous_metrics:
            threshold = self.thresholds.get(metric_name, 0.05)
            delta = round(current_val - baseline_val, 4)
            metrics_compared[metric_name] = {
                "baseline": baseline_val,
                "current": current_val,
                "delta": delta,
                "threshold": threshold,
                "drifted": delta < -threshold,
            }

            if delta < -threshold:
                severity = AlertSeverity.CRITICAL if abs(delta) >= 0.15 else AlertSeverity.WARNING
                alert = QualityDriftAlert(
                    alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
                    metric=metric_name,
                    baseline_value=round(baseline_val, 4),
                    current_value=round(current_val, 4),
                    threshold=threshold,
                    observed_delta=delta,
                    severity=severity,
                    message=(
                        f"Quality drift detected: '{metric_name}' degraded by "
                        f"{abs(delta):.4f} (threshold: {threshold}). "
                        f"Baseline: {baseline_val:.4f} → Current: {current_val:.4f}."
                    ),
                    benchmark_id=current.benchmark_id,
                    run_id=current.run_id,
                    details={
                        "baseline_benchmark_id": baseline.benchmark_id,
                        "current_benchmark_id": current.benchmark_id,
                    },
                )
                self.alert_repo.insert(alert)
                alerts.append(alert)
                logger.warning(f"[DriftAlert] {alert.message}")

        # --- Safety violations (absolute count delta — never merged into quality score) ---
        safety_delta = current.safety_violations - baseline.safety_violations
        metrics_compared["safety_violations"] = {
            "baseline": baseline.safety_violations,
            "current": current.safety_violations,
            "delta": safety_delta,
            "threshold": SAFETY_FAILURE_THRESHOLD,
            "drifted": safety_delta >= SAFETY_FAILURE_THRESHOLD,
        }

        if safety_delta >= SAFETY_FAILURE_THRESHOLD:
            alert = QualityDriftAlert(
                alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
                metric="safety_violations",
                baseline_value=float(baseline.safety_violations),
                current_value=float(current.safety_violations),
                threshold=float(SAFETY_FAILURE_THRESHOLD),
                observed_delta=float(safety_delta),
                severity=AlertSeverity.CRITICAL,
                message=(
                    f"SAFETY DRIFT DETECTED: {safety_delta} new safety violation(s) observed. "
                    f"Baseline: {baseline.safety_violations} → Current: {current.safety_violations}. "
                    f"Safety violations must be investigated immediately."
                ),
                benchmark_id=current.benchmark_id,
                run_id=current.run_id,
                details={
                    "baseline_benchmark_id": baseline.benchmark_id,
                    "current_benchmark_id": current.benchmark_id,
                    "note": "Safety violations are tracked separately from quality metrics.",
                },
            )
            self.alert_repo.insert(alert)
            alerts.append(alert)
            logger.error(f"[SafetyDriftAlert] {alert.message}")

        # --- Tool failures (count delta) ---
        tool_failure_delta = current.tool_failures - baseline.tool_failures
        metrics_compared["tool_failures"] = {
            "baseline": baseline.tool_failures,
            "current": current.tool_failures,
            "delta": tool_failure_delta,
            "threshold": TOOL_FAILURE_THRESHOLD,
            "drifted": tool_failure_delta >= TOOL_FAILURE_THRESHOLD,
        }

        if tool_failure_delta >= TOOL_FAILURE_THRESHOLD:
            alert = QualityDriftAlert(
                alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
                metric="tool_failures",
                baseline_value=float(baseline.tool_failures),
                current_value=float(current.tool_failures),
                threshold=float(TOOL_FAILURE_THRESHOLD),
                observed_delta=float(tool_failure_delta),
                severity=AlertSeverity.WARNING,
                message=(
                    f"Tool failure drift detected: {tool_failure_delta} new tool failure(s). "
                    f"Baseline: {baseline.tool_failures} → Current: {current.tool_failures}."
                ),
                benchmark_id=current.benchmark_id,
                run_id=current.run_id,
                details={
                    "baseline_benchmark_id": baseline.benchmark_id,
                    "current_benchmark_id": current.benchmark_id,
                },
            )
            self.alert_repo.insert(alert)
            alerts.append(alert)
            logger.warning(f"[ToolFailureDriftAlert] {alert.message}")

        # --- Integration failures (count delta) ---
        integration_failure_delta = current.integration_failures - baseline.integration_failures
        metrics_compared["integration_failures"] = {
            "baseline": baseline.integration_failures,
            "current": current.integration_failures,
            "delta": integration_failure_delta,
            "drifted": integration_failure_delta > 0,
        }

        if integration_failure_delta > 0:
            alert = QualityDriftAlert(
                alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
                metric="integration_failures",
                baseline_value=float(baseline.integration_failures),
                current_value=float(current.integration_failures),
                threshold=1.0,
                observed_delta=float(integration_failure_delta),
                severity=AlertSeverity.WARNING,
                message=(
                    f"Integration failure drift detected: {integration_failure_delta} new integration failure(s). "
                    f"Baseline: {baseline.integration_failures} → Current: {current.integration_failures}."
                ),
                benchmark_id=current.benchmark_id,
                run_id=current.run_id,
                details={
                    "baseline_benchmark_id": baseline.benchmark_id,
                    "current_benchmark_id": current.benchmark_id,
                },
            )
            self.alert_repo.insert(alert)
            alerts.append(alert)

        drift_detected = len(alerts) > 0

        result = DriftCheckResult(
            baseline_benchmark_id=baseline.benchmark_id,
            current_benchmark_id=current.benchmark_id,
            alerts_generated=alerts,
            metrics_compared=metrics_compared,
            drift_detected=drift_detected,
        )

        if drift_detected:
            logger.warning(
                f"[QualityDrift] Drift detected comparing {baseline.benchmark_id} → "
                f"{current.benchmark_id}: {len(alerts)} alert(s) generated."
            )
        else:
            logger.info(
                f"[QualityDrift] No drift detected: {baseline.benchmark_id} → {current.benchmark_id}."
            )

        return result
