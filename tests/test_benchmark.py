"""
Tests for BenchmarkEngine and Golden Dataset Benchmarking.
"""

from evaluation.benchmark import BenchmarkEngine
from simulator.mock_agent import MockHealthcareAgent


def test_benchmark_engine_execution():
    engine = BenchmarkEngine()
    agent = MockHealthcareAgent()

    benchmark_res = engine.run_benchmark(agent=agent, benchmark_id="BMK-TEST-001")

    assert benchmark_res.benchmark_id == "BMK-TEST-001"
    assert benchmark_res.golden_dataset_version == "1.0.0"
    assert benchmark_res.total_scenarios >= 21
    assert benchmark_res.passed_count > 0
    assert benchmark_res.accuracy > 0.0
    assert len(benchmark_res.scenario_level_results) == benchmark_res.total_scenarios
    # Ensure safety violations and tool failures remain separate fields
    assert hasattr(benchmark_res, "safety_violations")
    assert hasattr(benchmark_res, "tool_failures")
    assert hasattr(benchmark_res, "integration_failures")
