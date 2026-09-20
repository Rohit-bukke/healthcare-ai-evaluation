"""
Tests for Regression Engine and Degradation Detection.
"""

from evaluation.benchmark import BenchmarkEngine
from evaluation.regression import RegressionEngine, REGRESSION_THRESHOLDS
from evaluation.repositories.benchmark_repo import BenchmarkResult
from simulator.mock_agent import MockHealthcareAgent
from simulator.degraded_agent import DegradedHealthcareAgent


def test_regression_identical_benchmarks():
    bmk_engine = BenchmarkEngine()
    agent = MockHealthcareAgent()

    b1 = bmk_engine.run_benchmark(agent=agent, benchmark_id="BMK-BASE-1")
    b2 = bmk_engine.run_benchmark(agent=agent, benchmark_id="BMK-BASE-2")

    reg_engine = RegressionEngine()
    reg_result = reg_engine.compare_benchmarks(b1, b2)

    assert reg_result.status == "no_regression"
    assert reg_result.regressions_detected is False
    assert reg_result.accuracy_delta == 0.0
    assert len(reg_result.new_failures) == 0


def test_regression_degraded_benchmark_detection():
    bmk_engine = BenchmarkEngine()
    baseline_agent = MockHealthcareAgent()
    degraded_agent = DegradedHealthcareAgent()

    b_base = bmk_engine.run_benchmark(agent=baseline_agent, benchmark_id="BMK-BASE")
    b_degraded = bmk_engine.run_benchmark(agent=degraded_agent, benchmark_id="BMK-DEGRADED")

    reg_engine = RegressionEngine()
    reg_result = reg_engine.compare_benchmarks(b_base, b_degraded)

    assert reg_result.status == "regression_detected"
    assert reg_result.regressions_detected is True
    assert reg_result.accuracy_delta < 0.0
    assert len(reg_result.new_failures) > 0


def test_regression_metric_threshold_sensitivity():
    b_base = BenchmarkResult(
        benchmark_id="BMK-1",
        run_id="R1",
        total_scenarios=20,
        passed_count=20,
        accuracy=1.0,
        tool_correctness=1.0,
        argument_correctness=1.0,
        grounding_accuracy=1.0,
        scenario_level_results=[{"scenario_id": f"SCN-{i:03d}", "status": "pass"} for i in range(1, 21)]
    )

    # Simulated drop in accuracy > 0.05
    b_cur = BenchmarkResult(
        benchmark_id="BMK-2",
        run_id="R2",
        total_scenarios=20,
        passed_count=18,
        accuracy=0.90,  # 0.10 drop > 0.05 threshold
        tool_correctness=1.0,
        argument_correctness=1.0,
        grounding_accuracy=1.0,
        scenario_level_results=[
            {"scenario_id": "SCN-001", "status": "fail"},
            {"scenario_id": "SCN-002", "status": "fail"}
        ] + [{"scenario_id": f"SCN-{i:03d}", "status": "pass"} for i in range(3, 21)]
    )

    reg_engine = RegressionEngine()
    reg_res = reg_engine.compare_benchmarks(b_base, b_cur)

    assert reg_res.status == "regression_detected"
    assert reg_res.accuracy_delta == -0.10
    assert "SCN-001" in reg_res.new_failures
    assert "SCN-002" in reg_res.new_failures


def test_regression_recovered_failures_detection():
    b_base = BenchmarkResult(
        benchmark_id="BMK-1",
        run_id="R1",
        total_scenarios=10,
        passed_count=8,
        accuracy=0.8,
        scenario_level_results=[{"scenario_id": "SCN-001", "status": "fail"}] + [{"scenario_id": f"SCN-{i:03d}", "status": "pass"} for i in range(2, 11)]
    )

    b_cur = BenchmarkResult(
        benchmark_id="BMK-2",
        run_id="R2",
        total_scenarios=10,
        passed_count=10,
        accuracy=1.0,
        scenario_level_results=[{"scenario_id": f"SCN-{i:03d}", "status": "pass"} for i in range(1, 11)]
    )

    reg_engine = RegressionEngine()
    reg_res = reg_engine.compare_benchmarks(b_base, b_cur)

    assert "SCN-001" in reg_res.recovered_failures
