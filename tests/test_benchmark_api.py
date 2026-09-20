"""
Tests for Benchmark and Regression API Endpoints.
"""


def test_run_benchmark_api_baseline(client):
    response = client.post("/api/v1/benchmarks/run")
    assert response.status_code == 200
    data = response.json()
    assert "benchmark_id" in data
    assert data["golden_dataset_version"] == "1.0.0"
    assert data["total_scenarios"] >= 21
    assert data["accuracy"] > 0.0


def test_run_benchmark_api_degraded(client):
    response = client.post("/api/v1/benchmarks/run?degraded=true")
    assert response.status_code == 200
    data = response.json()
    assert "benchmark_id" in data
    assert data["agent_id"] == "degraded_healthcare_agent_v1"


def test_run_regression_api(client):
    response = client.post("/api/v1/benchmarks/regression")
    assert response.status_code == 200
    data = response.json()
    assert "regression_id" in data
    assert data["status"] in ["no_regression", "regression_detected"]
    assert "regressions_detected" in data


def test_list_benchmarks_api(client):
    response = client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    bmks = response.json()
    assert isinstance(bmks, list)


def test_list_regressions_api(client):
    response = client.get("/api/v1/benchmarks/regressions")
    assert response.status_code == 200
    regs = response.json()
    assert isinstance(regs, list)
