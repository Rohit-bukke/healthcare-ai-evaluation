"""
Tests for API Endpoints & Benchmark Execution.
"""


def test_get_dashboard_html(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Healthcare AI Evaluation & Quality Dashboard" in response.text


def test_get_dashboard_summary_api(client):
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_runs" in data
    assert "overall_accuracy" in data
    assert "tool_correctness" in data


def test_list_scenarios_api(client):
    response = client.get("/api/v1/evaluations/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 21


def test_get_scenario_by_id_api(client):
    response = client.get("/api/v1/evaluations/scenarios/SCN-017")
    assert response.status_code == 200
    sc = response.json()
    assert sc["scenario_id"] == "SCN-017"
    assert sc["category"] == "urgent_symptoms"


def test_execute_single_scenario_api(client):
    response = client.post("/api/v1/evaluations/run-scenario/SCN-001")
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["status"] == "completed"
    assert run_data["total_scenarios"] == 1


def test_execute_category_api(client):
    response = client.post("/api/v1/evaluations/run-category/urgent_symptoms")
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["status"] == "completed"
    assert run_data["total_scenarios"] >= 1


def test_execute_full_dataset_api(client):
    response = client.post("/api/v1/evaluations/run-dataset")
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["status"] == "completed"
    assert run_data["total_scenarios"] >= 21
    run_id = run_data["run_id"]

    # Query detailed results for run
    res_response = client.get(f"/api/v1/evaluations/results/{run_id}")
    assert res_response.status_code == 200
    results = res_response.json()
    assert len(results) >= 21


def test_list_findings_api(client):
    response = client.get("/api/v1/findings")
    assert response.status_code == 200
    findings = response.json()
    assert isinstance(findings, list)


def test_invalid_scenario_api_404(client):
    response = client.post("/api/v1/evaluations/run-scenario/INVALID-999")
    assert response.status_code == 404
