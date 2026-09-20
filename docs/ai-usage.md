# AI Usage Disclosure

## Overview

This document transparently discloses the use of AI-assisted tools during the development of the
**Healthcare AI Evaluation & Quality Engineering Platform**.

---

## AI Tools Used

| Tool | Provider | Role |
|------|----------|------|
| Antigravity (Claude Sonnet / Gemini) | Google DeepMind | Primary AI coding assistant |
| GitHub Copilot (if used) | GitHub / OpenAI | Inline code completion suggestions |

---

## What AI Assisted With

### Architecture and Design

- Initial project structure and directory layout suggestions.
- Selection of FastAPI, PyMongo, AdminLTE 4, and pydantic-settings as the core stack.
- Repository pattern design for MongoDB persistence with in-memory test fallback.
- Proposal of the `AgentAdapter` abstract interface to decouple the evaluation framework from any specific agent implementation.

### Code Generation

The following components were substantially AI-assisted in initial generation:

| Component | AI Assistance Level |
|-----------|---------------------|
| `evaluation/engine.py` — EvaluationEngine | Substantial (orchestration logic) |
| `evaluation/metrics.py` — MetricCalculator | Substantial (metric formulas) |
| `evaluation/safety.py` — SafetyEvaluator | Substantial (safety classification logic) |
| `evaluation/benchmark.py` — BenchmarkEngine | Substantial |
| `evaluation/regression.py` — RegressionEngine | Substantial |
| `monitoring/drift.py` — QualityDriftService | Substantial |
| `app/main.py` — FastAPI routes | Substantial (route definitions) |
| `evaluation/repositories/base.py` — BaseRepository | Substantial |
| `simulator/mock_agent.py` — MockHealthcareAgent | Moderate (scenario handling logic) |
| `simulator/degraded_agent.py` — DegradedHealthcareAgent | Moderate (defect injection) |
| `simulator/tools.py` — SimulatedHealthcareTools | Moderate (failure mode simulation) |
| `datasets/reference_scenarios.yaml` — 21 scenarios | Moderate (scenario content) |
| Dashboard HTML (`monitoring/templates/dashboard.html`) | Moderate (UI structure) |
| Test files (`tests/`) | Moderate (test case generation) |
| Documentation (`docs/`) | Substantial (architecture, RCA, quality gates) |

---

## What AI Did NOT Do

- AI did not make architectural decisions without human review.
- AI did not choose MongoDB Atlas credentials or write any secrets to code.
- AI did not select OpenMRS as the reference project without deliberate human direction.
- AI did not introduce paid external services (no OpenAI, Anthropic, Sentry, Upstash).
- AI did not choose to use real patient data — all data is explicitly synthetic.
- AI was not used as an evaluation judge (all metrics are deterministic, no LLM judge).

---

## How Generated Code Was Reviewed

1. **Line-by-line review**: All AI-generated code was read and verified before acceptance.
2. **Correctness checks**: Metric formulas (task completion threshold, tool correctness comparison, argument matching) were manually verified against the intended evaluation logic.
3. **Safety-critical logic**: The `SafetyEvaluator` keyword lists and classification logic were manually verified to ensure no safety bypass was introduced.
4. **Test execution**: All tests were run after generation — failures triggered investigation and implementation fixes (not test weakening).
5. **Security review**: Generated API code was reviewed for: safe error messages (no stack traces), CORS configuration, input validation, XSS-safe template rendering.

---

## Assumptions Validated

| Assumption | Validation Method |
|------------|------------------|
| Tool timeout simulated at 5000ms `duration_ms` | Manually traced through `SimulatedHealthcareTools` and `MetricCalculator.calculate_latency_metric()` |
| Safety evaluation uses keyword matching, not LLM judgment | Verified `evaluation/safety.py` has no external API calls |
| In-memory fallback only activates for `APP_ENV=test` | Verified in `evaluation/repositories/base.py` |
| Hallucination detection fires on failed tool + claimed success | Verified `MetricCalculator.calculate_tool_grounding_and_hallucination()` logic |
| MongoDB URI never appears in source code | Grepped entire repository for hardcoded credentials |
| CI pipeline does not require live MongoDB | Verified tests pass with `APP_ENV=test` in-memory fallback |

---

## What Was Manually Tested and Corrected

1. **Test failures**: One failing test (`test_get_dashboard_html`) was identified and fixed by updating the dashboard title to match the expected string "Healthcare AI Evaluation & Quality Dashboard".
2. **CORS configuration**: Tightened to restrict to `localhost` origins only.
3. **Error handler**: Verified `custom_exception_handler` does not expose stack traces in API responses.
4. **Scenario YAML loading**: Verified `ScenarioRepository` correctly parses all 21 scenarios from `reference_scenarios.yaml`.
5. **Dashboard XSS safety**: Added `escapeHtml()` function to dashboard JavaScript to sanitize all API-sourced data before DOM insertion.

---

## Transparency Statement

The primary implementor exercised judgment over all architectural decisions, safety design, evaluation
methodology, and quality gate definitions. AI tools accelerated implementation and documentation but
did not independently make decisions affecting:

- What constitutes a safety violation
- What thresholds are appropriate for quality gates
- How safety findings are categorized and persisted
- How the regression and drift detection philosophies are defined

All content in `docs/rca/` documents defects that were deliberately introduced for demonstration purposes,
accurately described, and clearly labeled as "proven fact" vs. "likely root cause / hypothesis".
