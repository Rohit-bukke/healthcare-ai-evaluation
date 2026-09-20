# Healthcare AI Evaluation Platform — Architecture Documentation

## Overview

This document describes the architecture of the **Healthcare AI Evaluation & Quality Engineering Platform**,
a deterministic, reproducible system for evaluating AI agents in simulated healthcare workflows.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│               Healthcare Evaluation Scenarios                        │
│         datasets/reference_scenarios.yaml (21 scenarios)            │
│         datasets/golden_dataset.yaml (version-controlled baseline)   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│               Conversation Simulator                                 │
│         simulator/simulator.py — ConversationSimulator               │
│         Executes multi-turn conversations against any AgentAdapter   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│             Healthcare Agent Adapter Layer                           │
│  simulator/adapter.py — AgentAdapter (abstract interface)           │
│  simulator/mock_agent.py — MockHealthcareAgent (normal behavior)    │
│  simulator/degraded_agent.py — DegradedHealthcareAgent (defects)   │
│  simulator/tools.py — SimulatedHealthcareTools                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Evaluation Engine                                   │
│         evaluation/engine.py — EvaluationEngine                     │
│         Orchestrates scenario execution, metrics, safety evaluation  │
│         Persists EvaluationRun and EvaluationResult to MongoDB      │
└──────────────────┬────────────────────────────────┬─────────────────┘
                   │                                │
                   ▼                                ▼
┌──────────────────────────┐          ┌─────────────────────────────┐
│  Metrics Calculation     │          │  Safety Evaluation           │
│  evaluation/metrics.py   │          │  evaluation/safety.py        │
│  - Task Completion       │          │  - Emergency escalation       │
│  - Tool Correctness      │          │  - Scope refusal             │
│  - Argument Correctness  │          │  - Privacy / PHI             │
│  - Grounding / Halluc.   │          │  - Prompt injection guard    │
│  - Latency               │          │  Always tracked separately   │
└──────────────────────────┘          └─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Benchmark Engine                                │
│         evaluation/benchmark.py — BenchmarkEngine                   │
│         Runs golden dataset benchmark, aggregates BenchmarkResult   │
│         Persists to MongoDB benchmark_results collection            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Regression Detection Engine                        │
│         evaluation/regression.py — RegressionEngine                 │
│         Compares baseline vs current BenchmarkResult                │
│         Detects metric degradation and scenario-level failures       │
│         Persists RegressionResult to MongoDB                        │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│               Monitoring / Quality Drift Detection                   │
│         monitoring/drift.py — QualityDriftService                   │
│         Compares current benchmark against fixed baseline snapshot  │
│         Generates QualityDriftAlert records per metric              │
│         Safety violations tracked as CRITICAL, never merged          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Findings / RCA / Quality Alerts                         │
│  app/models/finding.py — Finding (bug register with RCA fields)     │
│  app/models/alert.py — QualityDriftAlert                            │
│  evaluation/repositories/finding_repo.py — FindingRepository        │
│  evaluation/repositories/alert_repo.py — AlertRepository            │
│  docs/rca/ — Root Cause Analysis reports (Markdown)                 │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│              FastAPI REST API + AdminLTE Dashboard                   │
│  app/main.py — FastAPI application (all API routes)                 │
│  GET /dashboard — AdminLTE 4 Quality Dashboard (HTML)               │
│  GET /api/v1/dashboard/summary — Aggregated metrics for UI          │
│  POST /api/v1/benchmarks/run — Run benchmark                        │
│  POST /api/v1/benchmarks/regression — Run regression detection      │
│  POST /api/v1/monitoring/check-drift — Run drift detection          │
│  GET  /api/v1/monitoring/alerts — List quality drift alerts         │
│  GET  /api/v1/findings — List findings register                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### 1. Scenario Dataset Layer

| File | Purpose |
|------|---------|
| `datasets/reference_scenarios.yaml` | 21 version-controlled healthcare evaluation scenarios |
| `datasets/golden_dataset.yaml` | Version tag for benchmark baseline tracking |

Scenarios cover:
- Appointment scheduling, availability, modification, cancellation
- Tool failures (timeout, malformed, empty result)
- Safety: urgent symptoms, medication scope, PHI privacy, prompt injection
- Edge cases: ambiguous requests, duplicate booking, unavailable slots

### 2. Simulator Layer

| File | Purpose |
|------|---------|
| `simulator/adapter.py` | Abstract `AgentAdapter` interface — decouples evaluation from agent |
| `simulator/mock_agent.py` | `MockHealthcareAgent` — deterministic normal behavior |
| `simulator/degraded_agent.py` | `DegradedHealthcareAgent` — intentional defects for regression demo |
| `simulator/simulator.py` | `ConversationSimulator` — executes multi-turn conversations |
| `simulator/tools.py` | `SimulatedHealthcareTools` — five healthcare tools with failure modes |

Simulated tools:
- `check_availability(doctor, date)` — checks appointment slots
- `book_appointment(doctor, patient, dob, date, time)` — books appointments
- `cancel_appointment(apt_id)` — cancels appointments
- `reschedule_appointment(apt_id, new_date, new_time)` — reschedules
- `get_appointment_info(apt_id)` — retrieves appointment details

### 3. Evaluation Engine

| File | Purpose |
|------|---------|
| `evaluation/engine.py` | Main orchestrator — runs scenarios, computes metrics, persists results |
| `evaluation/metrics.py` | Five deterministic metric calculators |
| `evaluation/safety.py` | Safety evaluator — four safety expectation modes |

Metrics computed per scenario:
1. **Task Completion** — Did the agent complete the user's request?
2. **Tool Call Correctness** — Was the correct tool invoked?
3. **Tool Argument Correctness** — Were the tool arguments correct?
4. **Tool-Result Grounding / Hallucination Detection** — Did the agent hallucinate success after tool failure?
5. **Latency Evaluation** — Was response time within the 3000ms threshold?
6. **Safety Evaluation** — Evaluated separately from accuracy, never collapsed

### 4. Benchmark Engine

`evaluation/benchmark.py` — Reuses `EvaluationEngine`, builds a `BenchmarkResult` aggregate:
- Golden dataset version tracking
- Per-scenario and aggregate metrics
- Tool and integration failure counts

### 5. Regression Detection Engine

`evaluation/regression.py` — Compares two `BenchmarkResult` objects:
- Detects metric degradation beyond explicit thresholds (accuracy: ≥5%, tool correctness: ≥5%)
- Tracks new scenario failures vs. recovered failures
- Tracks new safety violations, tool failures, integration failures separately

### 6. Quality Drift Detection (Monitoring)

`monitoring/drift.py` — Monitoring-level interpretation:
- Distinct from `RegressionEngine` (which compares two specific benchmarks)
- Compares current benchmark against a documented baseline snapshot
- Generates and persists `QualityDriftAlert` records
- Safety violations always generate `CRITICAL` alerts regardless of threshold
- Never collapses safety into a generic quality score

### 7. Repository Layer (MongoDB Persistence)

All repositories implement `BaseRepository[T]` from `evaluation/repositories/base.py`:
- Primary storage: **MongoDB** (via PyMongo)
- Test fallback: **in-memory dict** (only when `APP_ENV=test`)
- No data is lost between repository instances sharing the same MongoDB

| Collection | Repository | Purpose |
|------------|-----------|---------|
| `evaluation_runs` | `EvaluationRunRepository` | Evaluation run summaries |
| `evaluation_results` | `EvaluationResultRepository` | Per-scenario detailed results |
| `scenarios` | `ScenarioRepository` | Loaded evaluation scenarios |
| `conversations` | `ConversationRepository` | Conversation turns |
| `tool_calls` | `ToolCallRepository` | Tool invocation records |
| `findings` | `FindingRepository` | Bug register / safety findings |
| `benchmark_results` | `BenchmarkResultRepository` | Benchmark aggregates |
| `regression_results` | `RegressionResultRepository` | Regression detection results |
| `quality_drift_alerts` | `AlertRepository` | Quality drift alerts |

### 8. FastAPI API Layer

`app/main.py` provides all REST endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health + MongoDB connectivity check |
| GET | `/` or `/dashboard` | AdminLTE 4 dashboard HTML |
| GET | `/api/v1/dashboard/summary` | Aggregated metrics for dashboard |
| GET | `/api/v1/evaluations/scenarios` | List scenarios (optional category filter) |
| POST | `/api/v1/evaluations/run-dataset` | Run full evaluation |
| POST | `/api/v1/evaluations/run-scenario/{id}` | Run single scenario |
| POST | `/api/v1/evaluations/run-category/{cat}` | Run scenario category |
| POST | `/api/v1/benchmarks/run` | Run benchmark (normal or degraded) |
| POST | `/api/v1/benchmarks/regression` | Run regression detection |
| GET | `/api/v1/benchmarks` | List benchmarks |
| GET | `/api/v1/benchmarks/{id}` | Get benchmark by ID |
| POST | `/api/v1/monitoring/check-drift` | Run quality drift check |
| GET | `/api/v1/monitoring/alerts` | List quality drift alerts |
| GET | `/api/v1/findings` | List findings (filterable) |
| GET | `/api/v1/findings/{id}` | Get finding by ID |

---

## Key Design Decisions

### Deterministic Evaluation
All evaluation, benchmarking, regression, and drift detection is deterministic and reproducible.
No AI judge, LLM calls, or external services are required for tests to pass.

### Safety Always Separate
Safety violations are **never** folded into an overall accuracy or quality score.
They are tracked independently, displayed separately in the dashboard, and always generate `CRITICAL` drift alerts.

### No Duplicate Frameworks
- `RegressionEngine` compares two specific benchmark runs.
- `QualityDriftService` interprets a current benchmark against a baseline and generates persistent alerts.
- These serve complementary, distinct purposes.

### In-Memory Test Fallback
Test isolation is achieved by setting `APP_ENV=test`, which enables the in-memory fallback in `BaseRepository`.
Tests do **not** require a live MongoDB connection.

### No Hard-Coded Secrets
All configuration (MongoDB URI, database name) is loaded from environment variables or `.env` file via `pydantic-settings`.
No credentials appear in source code.

---

## Deployment Flow

```
git clone → venv → pip install -r requirements.txt
→ Configure .env (MONGODB_URI, DATABASE_NAME, APP_ENV)
→ python -m uvicorn app.main:app --reload --port 8000
→ Open http://localhost:8000/dashboard
```

Full workflow: see [README.md](../README.md)
