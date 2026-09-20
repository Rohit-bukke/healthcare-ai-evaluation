# RCA-002: Incorrect Tool Arguments for Appointment Booking

**RCA ID:** RCA-002
**Status:** Confirmed Defect (Reproduced via DegradedHealthcareAgent)
**Date:** 2026-09-19

---

## 1. Title

Incorrect Tool Arguments Passed to `book_appointment` During Standard Booking (SCN-003)

---

## 2. Scenario

**Scenario ID:** SCN-003
**Category:** `booking`
**Initial Prompt:** `"Please book the Monday 10:00 AM slot with Dr. Smith for John Doe (DOB: 1985-05-12, Phone: 555-3847)."`

---

## 3. Expected Behavior

The agent should invoke:
```
book_appointment(
  doctor="Dr. Smith",
  patient_name="John Doe",
  dob="1985-05-12",
  date="Monday",
  time="10:00 AM"
)
```

All four patient identity fields must match the scenario's expected arguments:
- `doctor`: Dr. Smith
- `patient_name`: John Doe
- `dob`: 1985-05-12
- `date`: Monday

---

## 4. Actual Behavior (Defect)

The degraded agent calls `book_appointment` with incorrect arguments:

```
book_appointment(
  doctor="Dr. Wrong",
  patient_name="Wrong Patient",
  dob="1900-01-01",
  date="Invalid Date"
)
```

**Tool name:** Correct (`book_appointment`)
**Arguments:** All four required fields are wrong (wrong provider, wrong patient, wrong DOB, wrong date).

---

## 5. Evidence

Reproduced deterministically via `DegradedHealthcareAgent.process_turns()`:
- Input trigger: `"please book the monday 10:00 am slot with dr. smith for john doe"`.
- `SimulatedHealthcareTools.book_appointment("Dr. Wrong", "Wrong Patient", "1900-01-01", "Invalid Date")` invoked.
- `argument_correctness = 0.0` in EvaluationResult for this scenario under the degraded agent.

**Benchmark metrics under DegradedHealthcareAgent:**
- Argument Correctness: FAIL (0/4 expected args matched)
- Tool Call Correctness: PASS (correct tool was `book_appointment`, which was called)
- Task Completion: PASS (tool returned without error — but with wrong data)

This is a **confirmed reproduced defect** — not a hypothesis.

---

## 6. Impact

**Clinical Impact:**
A booking is placed for the wrong patient, provider, date, and date of birth.
In a production system, this would create an appointment for a non-existent or wrong patient,
potentially exposing another patient's slot or creating phantom records.

**Regulatory Risk:**
Booking under a fabricated DOB (`1900-01-01`) may trigger validation errors in a real EHR system,
or silently create a corrupt record.

**Operational Impact:**
- Dr. Smith's schedule would not reflect the actual booking.
- John Doe would not receive confirmation.
- False positive: `task_completed = True` despite the appointment being for wrong patient/provider.

---

## 7. Reproduction Steps

```python
from simulator.degraded_agent import DegradedHealthcareAgent
from simulator.simulator import ConversationSimulator
from evaluation.repositories.scenario_repo import ScenarioRepository
from evaluation.metrics import MetricCalculator

agent = DegradedHealthcareAgent()
repo = ScenarioRepository()
sc = repo.get_by_id("SCN-003")
simulator = ConversationSimulator(agent)
result = simulator.execute_scenario(sc)

tc = result.agent_response.tool_calls[0]
print(tc.tool_name)       # book_appointment (correct)
print(tc.arguments)       # {"doctor": "Dr. Wrong", "patient_name": "Wrong Patient", ...}

arg_metric = MetricCalculator.calculate_argument_correctness(sc, result.agent_response)
print(arg_metric.score)   # 0.0
```

Or via API:
```bash
curl -X POST "http://localhost:8000/api/v1/benchmarks/run?degraded=true"
# Inspect scenario_level_results for SCN-003 -> argument_correctness = 0.0
```

---

## 8. Root Cause

> **Likely Root Cause (Hypothesis — supported by code inspection of `DegradedHealthcareAgent`)**

The `DegradedHealthcareAgent` explicitly substitutes wrong argument values for the pattern
`"please book the monday 10:00 am slot with dr. smith for john doe"`.

In a production agent, this class of argument correctness failure would most likely arise from:

1. Failure in entity extraction — the NLU component incorrectly parses provider name, patient name, or date.
2. Argument population from stale conversation state (using defaults or values from a prior turn).
3. Incorrect slot-filling in the dialogue state machine (fields populated from wrong conversation slots).

**Root Cause Confidence:** Confirmed as deliberate defect in `DegradedHealthcareAgent`. Likely root cause in production is NLU entity extraction failure or stale conversation state.

---

## 9. Recommended Remediation

1. Implement mandatory argument validation: reject `book_appointment` calls with obviously invalid DOBs (e.g., `1900-01-01`).
2. Implement entity extraction unit tests for DOB, provider name, patient name, and date parsing.
3. Add pre-execution argument sanity checks in the tool invocation layer.
4. Strengthen argument correctness regression test for SCN-003.

---

## 10. Validation Status

- ✅ Reproduced in evaluation framework (DegradedHealthcareAgent)
- ✅ Detected by RegressionEngine (argument_correctness regression)
- ✅ Detected by QualityDriftService (argument_correctness drift alert)
- ✅ Finding registered in FindingRepository
- ⏳ Production agent NLU remediation: pending
