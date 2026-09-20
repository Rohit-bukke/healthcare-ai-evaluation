# Healthcare AI Evaluation & Quality Engineering Framework

A specialized, deterministic **Evaluation, Quality Assurance, Benchmarking, Regression Testing, Safety Guardrails, and Monitoring Framework** for Healthcare AI Agents.

This framework operates independently of the underlying AI agent implementation, providing standardized benchmarking, tool-call correctness verification, safety failure detection, root-cause analysis (RCA) finding generation, quality drift detection, security hardening, and an interactive AdminLTE 4 executive quality dashboard.

---

## 🌟 Key Features & Architecture Highlights

- **Decoupled Agent Adapter Architecture (`simulator.adapter.AgentAdapter`)**: Abstract interface supporting any healthcare AI agent (`MockHealthcareAgent`, `DegradedHealthcareAgent`, or production agents).
- **21-Category Benchmark Dataset (`datasets/reference_scenarios.yaml`)**: Version-controlled YAML dataset covering routine appointment workflows, tool edge cases/failures, urgent cardiac symptom triaging, medication scope limits, HIPAA authorization, prompt injection resistance, and clinical scope boundaries.
- **Controlled Clinical Tool Simulation (`simulator.tools.SimulatedHealthcareTools`)**: Realistic clinical tools (`check_availability`, `book_appointment`, `cancel_appointment`, `reschedule_appointment`, `get_appointment_info`) supporting controlled failure modes and arguments verification.
- **Multi-Metric Evaluation Engine (`evaluation.metrics.MetricCalculator`)**: Separate, deterministic metric tracking for Task Completion, Tool Selection Accuracy, Argument Precision, Tool Result Grounding, Latency, and Safety Protocol Compliance. Safety failures are strictly kept separate from general functional failures.
- **Regression Engine & Quality Drift Alerting (`evaluation.regression.RegressionEngine`)**: Baselines comparison, regression detection, quality drift calculations, and deterministic email/log alerts when drift thresholds are breached.
- **Findings & Bug Register (`evaluation.repositories.FindingRepository`)**: Auto-generated structured findings for failed evaluations, with severity classification (CRITICAL, HIGH, MEDIUM, LOW) and links to 5 pre-built Root Cause Analysis (RCA) reports.
- **Security Hardening (`app/security.py` & `app/middleware.py`)**: Strict security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options), robust input sanitization, non-root environment execution, and zero secret leakage.
- **AdminLTE 4 Quality Dashboard (`/dashboard`)**: Open-source Bootstrap 5 executive dashboard with Chart.js visualization, real-time KPI metrics, quality drift alert indicators, severity distribution charts, and interactive evaluation triggering.

---

## 🏗 System Architecture

```
                          +---------------------------------------+
                          |   AdminLTE 4 Executive Dashboard      |
                          |   (GET /dashboard, Chart.js, HTML5)   |
                          +-------------------+-------------------+
                                              |
                                              v
                          +-------------------+-------------------+
                          |     FastAPI REST API Layer            |
                          | (Security Headers, Rate Limit, Cors)  |
                          +-------------------+-------------------+
                                              |
                                              v
                          +-------------------+-------------------+
                          |    Benchmark & Regression Engine      |
                          |   (Quality Drift & Alerts Evaluator)  |
                          +--------+--------------------+---------+
                                   |                    |
                                   v                    v
      +----------------------------+----+   +-----------+--------------------+
      | Conversation Simulator          |   | PyMongo & In-Memory Repositories   |
      | (simulator/simulator.py)        |   | (Runs, Repos, Findings, Alerts)    |
      +----------------------------+----+   +------------------------------------+
                                   |
                                   v
      +----------------------------+----+
      | AgentAdapter interface          |
      | (MockHealthcareAgent / Degraded)|
      +---------------------------------+
```

---

## 📚 Documentation Index

- 📑 [Architecture Documentation](docs/architecture.md) — System components, data pipelines, database models, and design decisions.
- 🎯 [Project Selection](docs/project-selection.md) — Healthcare domain context (OpenMRS integration blueprint).
- 🛡️ [Quality Gates & Thresholds](docs/quality-gates.md) — Mandatory CI/CD release gating rules and blocker criteria.
- 🔬 [Root Cause Analysis (RCA) Reports](docs/rca/) — RCA-001 through RCA-005 detailed bug breakdowns.
- 🤖 [AI Usage Disclosure](docs/ai-usage.md) — Transparency disclosure on AI tools used during development.

---

## ⚡ Quick Start & Final Demo Workflow

### 1. Requirements & Setup
```bash
# Prerequisites: Python 3.10+
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
APP_ENV=development
PORT=8000
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=healthcare_ai_eval
```
*Note: In `test` mode (`APP_ENV=test`), all data operations seamlessly use in-memory repositories without needing live MongoDB credentials.*

### 3. Run the Server
```bash
python -m uvicorn app.main:app --port 8000 --reload
```

### 4. Open the Executive Quality Dashboard
Navigate to `http://localhost:8000/dashboard` in your browser to view metrics, active alerts, quality drift, and findings register.

### 5. Run Full Benchmark & Regression Suite via API
```bash
# Run benchmark
curl -X POST http://localhost:8000/api/v1/benchmark/run

# Run regression evaluation against baseline
curl -X POST http://localhost:8000/api/v1/regression/run

# Check active quality alerts
curl http://localhost:8000/api/v1/alerts
```

### 6. Run Automated Test Suite
```bash
python -m pytest -q
```

---

## 🛡️ Security & Hardening Features

- **Security Headers**: HSTS, CSP, X-Frame-Options (`DENY`), X-Content-Type-Options (`nosniff`), Referrer-Policy.
- **Input Sanitization**: Control character and script tag stripping across prompt inputs.
- **Zero Third-Party Secret Dependency**: Operates entirely offline / mock-based without requiring external LLM API keys (Gemini, OpenAI, Anthropic).

---

## 🧪 Benchmark Scenario Categories (21 Categories)

1. `appointment_request`
2. `appointment_availability`
3. `booking`
4. `cancellation`
5. `modification`
6. `appointment_info`
7. `ambiguous_request`
8. `incomplete_information`
9. `contradictory_followup`
10. `unavailable_appointment`
11. `duplicate_booking`
12. `empty_tool_result`
13. `malformed_tool_response`
14. `tool_timeout`
15. `tool_failure`
16. `unexpected_tool_response`
17. `urgent_symptoms` *(Safety - Urgent Cardiac Triage)*
18. `medication_request` *(Safety - Prescription Scope Limit)*
19. `unauthorized_phi` *(Safety - HIPAA/PHI Privacy Boundary)*
20. `prompt_injection` *(Safety - Jailbreak Resistance)*
21. `scope_violation` *(Safety - Unlicensed Clinical Diagnosis)*

---

## 📄 License & Attribution

Developed as a specialized Healthcare AI Quality Engineering & Evaluation Platform.
