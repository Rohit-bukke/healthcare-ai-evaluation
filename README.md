# Healthcare AI Evaluation & Quality Engineering Framework

A specialized, deterministic **Evaluation, Quality Assurance, Benchmarking, Regression, and Safety Layer** for Healthcare AI Agents.

This framework operates independently of the underlying AI agent implementation, providing standardized benchmarking, tool-call correctness verification, safety failure simulation, root-cause analysis (RCA) finding generation, and an AdminLTE 4 executive quality dashboard.

---

## Key Features & Capabilities

- **Agent Adapter Architecture (`simulator.adapter.AgentAdapter`)**: Decoupled interface supporting any healthcare agent implementation (Mock agent provided, real agent pluggable later).
- **Deterministic Mock Healthcare Agent (`simulator.mock_agent.MockHealthcareAgent`)**:
  - Supports 9 realistic clinical workflows: appointment requests, availability checks, bookings, cancellations, modifications, unavailable slots, ambiguous requests, missing patient info, contradictory follow-ups.
  - Simulates 6 failure modes: tool timeouts, EHR tool errors, malformed JSON responses, empty results, duplicate operations, and data conflicts.
- **Git Version-Controlled Datasets (`datasets/reference_scenarios.yaml`)**: Golden reference scenario dataset versioned directly inside Git.
- **PyMongo Repository Layer (`evaluation.repositories`)**: Production-ready MongoDB repository abstraction with connection pooling, index management, and instant in-memory fallback for offline/testing environments.
- **FastAPI Quality API & Health Checks (`app/main.py`)**: REST API endpoints for running benchmarks, listing scenarios, and fetching root-cause findings.
- **AdminLTE 4 Professional Admin Dashboard (`/dashboard`)**: Open-source Bootstrap 5 dashboard rendering accuracy gauges, tool correctness trends, latency stats, severity distribution charts, and recent evaluation run logs.
- **Deterministic pytest Suite (`tests/`)**: Complete test coverage across configuration, database, models, repositories, mock workflows, and API endpoints.

---

## Architecture Overview

```
                          +---------------------------------------+
                          |   AdminLTE 4 Quality Dashboard        |
                          |   (GET /dashboard, Chart.js, HTML5)   |
                          +-------------------+-------------------+
                                              |
                                              v
                          +-------------------+-------------------+
                          |     FastAPI REST API Layer            |
                          |     (app/main.py, /health, /api/v1)   |
                          +-------------------+-------------------+
                                              |
                                              v
                          +-------------------+-------------------+
                          |      Evaluation Engine                |
                          |   (evaluation/engine.py)              |
                          +--------+--------------------+---------+
                                   |                    |
                                   v                    v
      +----------------------------+----+   +-----------+--------------------+
      | AgentAdapter (simulator/adapter) |   | PyMongo Repositories & Git Datasets|
      +----------------------------+----+   | (evaluation/repositories/)       |
                                   |        +------------------------------------+
                                   v
      +----------------------------+----+
      | MockHealthcareAgent (simulator) |
      +---------------------------------+
```

---

## Directory Structure

```
healthcare-ai-evaluation/
├── app/
│   ├── __init__.py
│   ├── config.py              # pydantic-settings configuration (.env)
│   ├── database.py            # PyMongo client wrapper & ping health check
│   ├── main.py                # FastAPI endpoints & dashboard server
│   └── models/                # Domain models (Scenario, Turn, ToolCall, etc.)
├── evaluation/
│   ├── engine.py              # Evaluation benchmark orchestrator
│   └── repositories/          # Repositories for MongoDB & Git datasets
├── simulator/
│   ├── adapter.py             # AgentAdapter abstract base class
│   └── mock_agent.py          # Deterministic MockHealthcareAgent
├── datasets/
│   └── reference_scenarios.yaml # Version-controlled reference benchmark dataset
├── monitoring/
│   └── templates/
│       └── dashboard.html     # AdminLTE 4 (Bootstrap 5) UI
├── tests/                     # 100% deterministic pytest suite
└── README.md
```

---

## Prerequisites & Setup

### Prerequisites
- Python 3.12
- MongoDB (Local instance or MongoDB Atlas cluster)

### Environment Configuration (`.env`)

Create a local `.env` file based on `.env.example`:

```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=healthcare_ai_evaluation
APP_ENV=development
```

*(Note: `.env` is ignored by Git and will never be committed or exposed).*

---

## Running the Application

### 1. Start the FastAPI Application
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Access the Dashboard & API
- **AdminLTE 4 Dashboard**: `http://127.0.0.1:8000/dashboard`
- **Health Check Endpoint**: `http://127.0.0.1:8000/health`
- **OpenAPI Interactive Specs**: `http://127.0.0.1:8000/docs`

---

## Running the Test Suite

Execute the deterministic pytest suite:

```bash
pytest -q
```

All 32 tests will execute and pass without requiring external API keys.

---

## Current Limitations

- **LLM-as-a-Judge**: Gemini and OpenAI LLM judge integrations remain optional per design requirements.
- **Healthcare Agent Integration**: Real third-party healthcare AI agents must implement the `AgentAdapter` interface (`simulator.adapter.AgentAdapter`).
