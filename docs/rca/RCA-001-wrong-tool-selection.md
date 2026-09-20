# RCA-001: Wrong Tool Selected for Standard Cardiology Appointment

**RCA ID:** RCA-001
**Status:** Confirmed Defect (Reproduced via DegradedHealthcareAgent)
**Date:** 2026-09-19

---

## 1. Title

Wrong Tool Selected for Standard Cardiology Appointment Request (SCN-001)

---

## 2. Scenario

**Scenario ID:** SCN-001
**Category:** `appointment_request`
**Initial Prompt:** `"I need to schedule a cardiology consultation with Dr. Smith for next Monday."`

---

## 3. Expected Behavior

The agent should:
1. Invoke `check_availability(doctor="Dr. Smith", date="Monday")` to verify slot availability.
2. Invoke `book_appointment(doctor="Dr. Smith", patient_name="John Doe", dob="1985-05-12", date="Monday", time="10:00 AM")`.
3. Confirm booking with a valid appointment confirmation code (e.g. `APT-XXXXX`).

---

## 4. Actual Behavior (Defect)

The degraded agent invokes `cancel_appointment("APT-0000")` instead of `check_availability` + `book_appointment`.

**Observed response:**
```
Executed cancellation tool instead of checking cardiology availability.
```

**Tool called:** `cancel_appointment`
**Expected tool:** `check_availability` + `book_appointment`

---

## 5. Evidence

Reproduced deterministically via `DegradedHealthcareAgent.process_turns()`:
- Input trigger: `"cardiology consultation with dr. smith"` matched in prompt.
- `SimulatedHealthcareTools.cancel_appointment("APT-0000")` called instead of booking tools.
- `EvaluationEngine` records `tool_correctness = 0.0` for SCN-001 under degraded agent.
- Benchmark regression detects `tool_correctness_delta < -0.05` when comparing baseline vs degraded.

**Evaluation metric outcome:**
- Task Completion: FAIL (wrong tool, no booking confirmed)
- Tool Call Correctness: FAIL (0.0 — wrong tool)
- Argument Correctness: Not evaluated (wrong tool called)

This is a **confirmed reproduced defect** — not a hypothesis.

---

## 6. Impact

**Clinical Impact:** A patient requesting a cardiology consultation would not receive a booking.
The agent would process a cancellation of a non-existent appointment instead.

**Operational Impact:**
- Downstream appointment confirmation system would receive invalid cancellation requests.
- Patient would not receive confirmation code; follow-up care scheduling would fail.

---

## 7. Reproduction Steps

```python
from simulator.degraded_agent import DegradedHealthcareAgent
from simulator.simulator import ConversationSimulator
from evaluation.repositories.scenario_repo import ScenarioRepository

agent = DegradedHealthcareAgent()
repo = ScenarioRepository()
sc = repo.get_by_id("SCN-001")
simulator = ConversationSimulator(agent)
result = simulator.execute_scenario(sc)

print(result.agent_response.tool_calls[0].tool_name)
# Output: "cancel_appointment"
# Expected: "check_availability" then "book_appointment"
```

Or via API:
```bash
# Run baseline benchmark
curl -X POST "http://localhost:8000/api/v1/benchmarks/run"

# Run degraded benchmark
curl -X POST "http://localhost:8000/api/v1/benchmarks/run?degraded=true"

# Run regression detection
curl -X POST "http://localhost:8000/api/v1/benchmarks/regression"
```

---

## 8. Root Cause

> **Likely Root Cause (Hypothesis — confirmed by code inspection of `DegradedHealthcareAgent`)**

The `DegradedHealthcareAgent` contains a hardcoded dispatch rule that intercepts the pattern
`"cardiology consultation with dr. smith"` and routes to `cancel_appointment` instead of
the expected `check_availability + book_appointment` sequence.

In a production agent, this class of defect would most likely arise from:

1. Incorrect intent classification in the agent's routing logic (matching "consultation" to "cancellation" intent).
2. Stale or incorrect tool-selection heuristics in the agent backend.
3. Failure in a multi-turn dialogue state machine resetting to cancellation flow.

**Root Cause Confidence:** Confirmed in `DegradedHealthcareAgent` code; likely root cause in production is tool routing misconfiguration.

---

## 9. Recommended Remediation

1. Add explicit intent disambiguation tests that verify `check_availability` is invoked before any booking.
2. Add guardrail: the agent should never invoke `cancel_appointment` without an explicit cancellation intent in the user prompt.
3. Add regression test that asserts SCN-001 always produces `check_availability` or `book_appointment` tool calls.
4. Verify tool-selection scoring in production agent routing layer.

---

## 10. Validation Status

- ✅ Reproduced in evaluation framework (DegradedHealthcareAgent)
- ✅ Detected by RegressionEngine (tool_correctness regression)
- ✅ Detected by QualityDriftService (tool_correctness drift alert)
- ✅ Finding created in FindingRepository
- ⏳ Production agent remediation: pending
