"""
FastAPI Application Entrypoint.
Provides REST API endpoints and AdminLTE 4 Quality Dashboard.
"""

import os
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import db_manager
from app.models.scenario import Scenario
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.models.finding import Finding
from evaluation.engine import EvaluationEngine
from evaluation.repositories.scenario_repo import ScenarioRepository
from evaluation.repositories.evaluation_run_repo import EvaluationRunRepository
from evaluation.repositories.evaluation_repo import EvaluationResultRepository
from evaluation.repositories.finding_repo import FindingRepository

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Healthcare AI Evaluation & Quality Engineering Framework API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Repositories & Evaluation Engine
scenario_repo = ScenarioRepository()
run_repo = EvaluationRunRepository()
result_repo = EvaluationResultRepository()
finding_repo = FindingRepository()
engine = EvaluationEngine(
    scenario_repo=scenario_repo,
    run_repo=run_repo,
    result_repo=result_repo,
    finding_repo=finding_repo
)


@app.get("/health", tags=["Health"])
def health_check():
    """Basic health check endpoint validating app and database connectivity."""
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
    """Returns aggregated metrics, evaluation runs, and findings for the UI."""
    runs = run_repo.list_all(limit=10)
    findings = finding_repo.list_all(limit=20)

    total_runs = len(runs)
    overall_accuracy = sum(r.overall_accuracy for r in runs) / total_runs if total_runs > 0 else 0.0
    tool_correctness = sum(r.tool_correctness for r in runs) / total_runs if total_runs > 0 else 0.0
    avg_latency = sum(r.average_latency_ms for r in runs) / total_runs if total_runs > 0 else 0.0

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = str(f.severity.value if hasattr(f.severity, "value") else f.severity).lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

    return {
        "total_runs": total_runs,
        "overall_accuracy": overall_accuracy,
        "tool_correctness": tool_correctness,
        "average_latency_ms": avg_latency,
        "severity_counts": severity_counts,
        "runs": [r.model_dump(mode="json") for r in runs],
        "findings": [f.model_dump(mode="json") for f in findings],
    }


@app.get("/api/v1/scenarios", response_model=List[Scenario], tags=["Scenarios"])
def list_scenarios():
    """List all registered version-controlled scenarios."""
    return scenario_repo.list_all()


@app.get("/api/v1/evaluations", response_model=List[EvaluationRun], tags=["Evaluations"])
def list_evaluation_runs():
    """List recent evaluation runs."""
    return run_repo.list_all()


@app.post("/api/v1/runs/execute", response_model=EvaluationRun, tags=["Evaluations"])
def execute_evaluation_run(scenario_ids: Optional[List[str]] = None):
    """Triggers an evaluation run across scenarios."""
    try:
        run = engine.run_benchmark(scenario_ids=scenario_ids)
        return run
    except Exception as err:
        logger.error(f"Error executing evaluation run: {err}")
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/api/v1/findings", response_model=List[Finding], tags=["Findings"])
def list_findings():
    """List root-cause findings and safety issues."""
    return finding_repo.list_all()
