"""
FastAPI Application Entrypoint.
Provides REST API endpoints for Healthcare AI Evaluation, Benchmarking,
Regression Detection, Quality Drift Monitoring, and AdminLTE 4 Quality Dashboard.
"""

import os
import uuid
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.database import db_manager
from app.models.scenario import Scenario
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.models.finding import Finding, FindingStatus
from app.models.regression import RegressionResult
from app.models.alert import QualityDriftAlert, AlertStatus

from evaluation.engine import EvaluationEngine
from evaluation.benchmark import BenchmarkEngine
from evaluation.regression import RegressionEngine
from evaluation.repositories.scenario_repo import ScenarioRepository
from evaluation.repositories.evaluation_run_repo import EvaluationRunRepository
from evaluation.repositories.evaluation_repo import EvaluationResultRepository
from evaluation.repositories.finding_repo import FindingRepository
from evaluation.repositories.benchmark_repo import BenchmarkResultRepository, BenchmarkResult
from evaluation.repositories.regression_repo import RegressionResultRepository
from evaluation.repositories.alert_repo import AlertRepository

from monitoring.drift import QualityDriftService

from simulator.mock_agent import MockHealthcareAgent
from simulator.degraded_agent import DegradedHealthcareAgent

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Healthcare AI Evaluation, Benchmarking, Regression Detection & Quality Monitoring API"
)

# CORS middleware — restrict to localhost in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)

# Repositories & Engines
scenario_repo = ScenarioRepository()
run_repo = EvaluationRunRepository()
result_repo = EvaluationResultRepository()
finding_repo = FindingRepository()
benchmark_repo = BenchmarkResultRepository()
regression_repo = RegressionResultRepository()
alert_repo = AlertRepository()

eval_engine = EvaluationEngine(
    scenario_repo=scenario_repo,
    run_repo=run_repo,
    result_repo=result_repo,
    finding_repo=finding_repo
)

benchmark_engine = BenchmarkEngine(
    eval_engine=eval_engine,
    benchmark_repo=benchmark_repo
)

regression_engine = RegressionEngine(
    regression_repo=regression_repo,
    benchmark_repo=benchmark_repo
)

drift_service = QualityDriftService(alert_repo=alert_repo)


# Custom Exception Handler — safe error messages, no stack trace leakage
@app.exception_handler(Exception)
async def custom_exception_handler(request, exc):
    logger.error(f"API Error handling request {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "An internal system error occurred during evaluation."}
    )


@app.get("/health", tags=["Health"])
def health_check():
    """Basic health check endpoint validating app environment and MongoDB connectivity."""
    db_status = db_manager.ping()
    return {
        "status": "healthy",
        "app_env": settings.app_env,
        "version": settings.app_version,
        "database": db_status
    }


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    """Serves the AdminLTE 4 Professional Admin Dashboard UI."""
    template_path = os.path.join("monitoring", "templates", "dashboard.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Healthcare AI Evaluation Dashboard Template Not Found</h1>", status_code=404)


@app.get("/api/v1/dashboard/summary", tags=["Dashboard API"])
def get_dashboard_summary():
    """Returns aggregated metrics, evaluation runs, findings, and alerts for the UI."""
    runs = run_repo.list_all(limit=10)
    findings = finding_repo.list_all(limit=50)
    benchmarks = benchmark_repo.list_all(limit=5)
    alerts = alert_repo.list_all(limit=20)

    total_runs = len(runs)
    overall_accuracy = sum(r.overall_accuracy for r in runs) / total_runs if total_runs > 0 else 0.0
    tool_correctness = sum(r.tool_correctness for r in runs) / total_runs if total_runs > 0 else 0.0
    argument_correctness = sum(r.argument_correctness for r in runs) / total_runs if total_runs > 0 else 0.0
    grounding_accuracy = sum(r.grounding_accuracy for r in runs) / total_runs if total_runs > 0 else 0.0
    avg_latency = sum(r.average_latency_ms for r in runs) / total_runs if total_runs > 0 else 0.0
    total_safety_violations = sum(r.safety_violations_count for r in runs)
    total_tool_failures = sum(r.tool_failures_count for r in runs)
    total_integration_failures = sum(r.integration_failures_count for r in runs)

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    open_findings = 0
    for f in findings:
        sev = str(f.severity.value if hasattr(f.severity, "value") else f.severity).lower()
        if sev in severity_counts:
            severity_counts[sev] += 1
        if hasattr(f, 'status') and str(getattr(f.status, 'value', f.status)) == 'open':
            open_findings += 1

    latest_benchmark = benchmarks[0].model_dump(mode="json") if benchmarks else None
    open_alerts = [a for a in alerts if str(getattr(a.status, 'value', a.status)) == 'open']

    return {
        "total_runs": total_runs,
        "total_scenarios": sum(r.total_scenarios for r in runs),
        "overall_accuracy": round(overall_accuracy, 4),
        "tool_correctness": round(tool_correctness, 4),
        "argument_correctness": round(argument_correctness, 4),
        "grounding_accuracy": round(grounding_accuracy, 4),
        "average_latency_ms": round(avg_latency, 2),
        "safety_violations": total_safety_violations,
        "tool_failures": total_tool_failures,
        "integration_failures": total_integration_failures,
        "severity_counts": severity_counts,
        "open_findings": open_findings,
        "open_alerts": len(open_alerts),
        "latest_benchmark": latest_benchmark,
        "runs": [r.model_dump(mode="json") for r in runs],
        "findings": [f.model_dump(mode="json") for f in findings],
        "alerts": [a.model_dump(mode="json") for a in open_alerts],
    }


# Dataset & Scenario Endpoints
@app.get("/api/v1/evaluations/scenarios", response_model=List[Scenario], tags=["Scenarios"])
def list_scenarios(category: Optional[str] = Query(None, description="Filter by category")):
    """List registered version-controlled evaluation scenarios."""
    if category:
        return scenario_repo.get_by_category(category)
    return scenario_repo.list_all()


@app.get("/api/v1/evaluations/scenarios/{scenario_id}", response_model=Scenario, tags=["Scenarios"])
def get_scenario(scenario_id: str = Path(..., description="Scenario ID")):
    """Fetch single evaluation scenario details."""
    sc = scenario_repo.get_by_id(scenario_id)
    if not sc:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found.")
    return sc


# Benchmark & Regression API Endpoints
@app.post("/api/v1/benchmarks/run", response_model=BenchmarkResult, tags=["Benchmarks"])
def run_benchmark_endpoint(degraded: bool = Query(False, description="Run with DegradedHealthcareAgent for regression demo")):
    """Executes a version-controlled golden benchmark."""
    try:
        agent = DegradedHealthcareAgent() if degraded else MockHealthcareAgent()
        bmk = benchmark_engine.run_benchmark(agent=agent)
        return bmk
    except Exception as err:
        logger.error(f"Error executing benchmark run: {err}")
        raise HTTPException(status_code=500, detail="Benchmark execution failed.")


class RegressionRequest(BaseModel):
    baseline_id: Optional[str] = None
    current_id: Optional[str] = None


@app.post("/api/v1/benchmarks/regression", response_model=RegressionResult, tags=["Benchmarks"])
def run_regression_endpoint(
    baseline_id: Optional[str] = Query(None, description="Baseline Benchmark ID"),
    current_id: Optional[str] = Query(None, description="Current Benchmark ID")
):
    """
    Compares baseline and current benchmarks to detect quality regressions.
    If baseline_id or current_id are omitted, executes baseline vs degraded benchmark demo.
    """
    try:
        if not baseline_id:
            baseline_bmk = benchmark_engine.run_benchmark(agent=MockHealthcareAgent(), benchmark_id="BMK-BASELINE-DEFAULT")
        else:
            baseline_bmk = benchmark_repo.get_by_id(baseline_id)
            if not baseline_bmk:
                raise HTTPException(status_code=404, detail=f"Baseline benchmark {baseline_id} not found.")

        if not current_id:
            current_bmk = benchmark_engine.run_benchmark(agent=DegradedHealthcareAgent(), benchmark_id="BMK-DEGRADED-DEFAULT")
        else:
            current_bmk = benchmark_repo.get_by_id(current_id)
            if not current_bmk:
                raise HTTPException(status_code=404, detail=f"Current benchmark {current_id} not found.")

        reg_result = regression_engine.compare_benchmarks(baseline_bmk, current_bmk)
        return reg_result
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Error running regression detection: {err}")
        raise HTTPException(status_code=500, detail="Regression detection execution failed.")


@app.get("/api/v1/benchmarks", response_model=List[BenchmarkResult], tags=["Benchmarks"])
def list_benchmarks():
    """List executed benchmark results."""
    return benchmark_repo.list_all()


@app.get("/api/v1/benchmarks/regressions", response_model=List[RegressionResult], tags=["Benchmarks"])
def list_regressions():
    """List regression detection results."""
    return regression_repo.list_all()


@app.get("/api/v1/benchmarks/{benchmark_id}", response_model=BenchmarkResult, tags=["Benchmarks"])
def get_benchmark(benchmark_id: str = Path(..., description="Benchmark ID")):
    """Fetch benchmark result by ID."""
    bmk = benchmark_repo.get_by_id(benchmark_id)
    if not bmk:
        raise HTTPException(status_code=404, detail=f"Benchmark {benchmark_id} not found.")
    return bmk


@app.get("/api/v1/benchmarks/{benchmark_id}/results", tags=["Benchmarks"])
def get_benchmark_scenario_results(benchmark_id: str = Path(..., description="Benchmark ID")):
    """Fetch detailed scenario-level results for a benchmark."""
    bmk = benchmark_repo.get_by_id(benchmark_id)
    if not bmk:
        raise HTTPException(status_code=404, detail=f"Benchmark {benchmark_id} not found.")
    return bmk.scenario_level_results


# Monitoring — Drift Detection & Alerts
@app.post("/api/v1/monitoring/check-drift", tags=["Monitoring"])
def check_quality_drift(
    baseline_id: Optional[str] = Query(None, description="Baseline Benchmark ID"),
    current_id: Optional[str] = Query(None, description="Current Benchmark ID (defaults to degraded demo)")
):
    """
    Run quality drift check comparing baseline vs current benchmark.
    Generates and persists QualityDriftAlert records for any detected degradations.
    Safety violations, tool failures, and integration failures are tracked separately.
    """
    try:
        if not baseline_id:
            baseline_bmk = benchmark_engine.run_benchmark(agent=MockHealthcareAgent(), benchmark_id="BMK-DRIFT-BASELINE")
        else:
            baseline_bmk = benchmark_repo.get_by_id(baseline_id)
            if not baseline_bmk:
                raise HTTPException(status_code=404, detail=f"Baseline benchmark {baseline_id} not found.")

        if not current_id:
            current_bmk = benchmark_engine.run_benchmark(agent=DegradedHealthcareAgent(), benchmark_id="BMK-DRIFT-CURRENT")
        else:
            current_bmk = benchmark_repo.get_by_id(current_id)
            if not current_bmk:
                raise HTTPException(status_code=404, detail=f"Current benchmark {current_id} not found.")

        drift_result = drift_service.check_drift(baseline_bmk, current_bmk)
        return drift_result.to_dict()
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Drift check error: {err}")
        raise HTTPException(status_code=500, detail="Drift check execution failed.")


@app.get("/api/v1/monitoring/alerts", response_model=List[QualityDriftAlert], tags=["Monitoring"])
def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status: open, acknowledged, resolved"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical")
):
    """List quality drift alerts with optional filtering."""
    if status:
        return alert_repo.get_by_status(status)
    if severity:
        return alert_repo.get_by_severity(severity)
    return alert_repo.list_all(limit=100)


@app.post("/api/v1/monitoring/alerts/{alert_id}/acknowledge", tags=["Monitoring"])
def acknowledge_alert(alert_id: str = Path(..., description="Alert ID")):
    """Mark a quality drift alert as acknowledged."""
    from datetime import datetime, timezone
    alert = alert_repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert_repo.insert(alert)
    return {"status": "acknowledged", "alert_id": alert_id}


# Findings API
@app.get("/api/v1/findings", response_model=List[Finding], tags=["Findings"])
def list_findings(
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    status: Optional[str] = Query(None, description="Filter by status: open, under_investigation, remediated")
):
    """List findings from the findings register with optional filtering."""
    if run_id:
        return finding_repo.get_by_run_id(run_id)
    if severity:
        return finding_repo.get_by_severity(severity)
    if status:
        return finding_repo.get_by_status(status)
    return finding_repo.list_all(limit=100)


@app.get("/api/v1/findings/{finding_id}", response_model=Finding, tags=["Findings"])
def get_finding(finding_id: str = Path(..., description="Finding ID")):
    """Fetch a single finding by ID."""
    finding = finding_repo.get_by_id(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found.")
    return finding


# Legacy Evaluation API Endpoints
@app.post("/api/v1/evaluations/run-scenario/{scenario_id}", response_model=EvaluationRun, tags=["Evaluations"])
def execute_single_scenario(scenario_id: str = Path(..., description="Scenario ID to execute")):
    sc = scenario_repo.get_by_id(scenario_id)
    if not sc:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found.")
    try:
        run = eval_engine.run_benchmark(scenario_ids=[scenario_id])
        return run
    except Exception as err:
        logger.error(f"Error executing scenario {scenario_id}: {err}")
        raise HTTPException(status_code=500, detail="Evaluation execution failed.")


@app.post("/api/v1/evaluations/run-category/{category}", response_model=EvaluationRun, tags=["Evaluations"])
def execute_category_scenarios(category: str = Path(..., description="Category name to execute")):
    try:
        run = eval_engine.run_benchmark(category=category)
        if run.total_scenarios == 0:
            raise HTTPException(status_code=404, detail=f"No scenarios found for category '{category}'.")
        return run
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Error executing category {category}: {err}")
        raise HTTPException(status_code=500, detail="Category evaluation execution failed.")


@app.post("/api/v1/evaluations/run-dataset", response_model=EvaluationRun, tags=["Evaluations"])
@app.post("/api/v1/runs/execute", response_model=EvaluationRun, tags=["Evaluations"])
def execute_full_dataset():
    try:
        run = eval_engine.run_benchmark()
        return run
    except Exception as err:
        logger.error(f"Error executing full dataset evaluation: {err}")
        raise HTTPException(status_code=500, detail="Full dataset benchmark execution failed.")


@app.get("/api/v1/evaluations/runs/{run_id}", response_model=EvaluationRun, tags=["Evaluations"])
def get_evaluation_run(run_id: str = Path(..., description="Run ID")):
    run = run_repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id} not found.")
    return run


@app.get("/api/v1/evaluations/results/{run_id}", response_model=List[EvaluationResult], tags=["Evaluations"])
def get_evaluation_results(run_id: str = Path(..., description="Run ID")):
    results = result_repo.get_by_run_id(run_id)
    if not results:
        raise HTTPException(status_code=404, detail=f"No detailed results found for run {run_id}.")
    return results
