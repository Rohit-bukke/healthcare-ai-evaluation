"""
Tests for API Endpoints & Evaluation Engine Integration.
"""


def test_get_dashboard_html(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Healthcare AI Evaluation & Quality Dashboard" in response.text
    assert "AdminLTE" in response.text or "adminlte" in response.text


def test_get_dashboard_summary_api(client):
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_runs" in data
    assert "overall_accuracy" in data
    assert "tool_correctness" in data
    assert "runs" in data
    assert "findings" in data


def test_list_scenarios_api(client):
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 10


def test_execute_evaluation_run_api(client):
    response = client.post("/api/v1/runs/execute")
    assert response.status_code == 200
    run_data = response.json()
    assert run_data["status"] == "completed"
    assert run_data["total_scenarios"] >= 10
    assert "overall_accuracy" in run_data
    assert "run_id" in run_data


def test_list_findings_api(client):
    response = client.get("/api/v1/findings")
    assert response.status_code == 200
    findings = response.json()
    assert isinstance(findings, list)
