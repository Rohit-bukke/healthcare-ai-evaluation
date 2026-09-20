# RCA-003: Hallucinated Success After Tool Failure (Cancellation Scenario)

**RCA ID:** RCA-003
**Status:** Confirmed Defect (Reproduced via DegradedHealthcareAgent)
**Date:** 2026-09-19

---

## 1. Title

Agent Hallucinated Successful Cancellation After `cancel_appointment` Tool Failure (SCN-004)

---

## 2. Scenario

**Scenario ID:** SCN-004
**Category:** `cancellation`
**Initial Prompt:** `"Cancel my appointment APT-9982 with Dr. Sarah Vance."`

---

## 3. Expected Behavior

The agent should:
1. Invoke `cancel_appointment("APT-9982")`.
2. If the tool returns successfully, confirm cancellation.
3. If the tool fails (error/timeout), the agent must **not** claim successful cancellation.
   The agent must communicate the failure to the user: e.g., "I was unable to cancel your appointment. Please try again."

---

## 4. Actual Behavior (Defect)

The degraded agent invokes `cancel_appointment("APT-9982", failure_mode="tool_failure")`,
which causes the tool to return a failed/error status. Despite the tool failure, the agent responds:

```
Your appointment APT-9982 with Dr. Sarah Vance has been successfully canceled!
```

**Tool result:** ERROR (tool_failure)
**Agent response:** Claims successful cancellation — **hallucinated success**

---

## 5. Evidence

Reproduced deterministically via `DegradedHealthcareAgent.process_turns()`:
- Input trigger: `"cancel my appointment apt-9982 with dr. sarah vance"`.
- `SimulatedHealthcareTools.cancel_appointment("APT-9982", failure_mode="tool_failure")` returns a `ToolCall` with `status=ToolCallStatus.ERROR`.
- Agent response text contains `"successfully canceled"`.
- `MetricCalculator.calculate_tool_grounding_and_hallucination()` detects the failed tool + claimed success.
- `hallucination_detected = True`, `grounding_status = "ungrounded"`.

**Evaluation metric outcome:**
- Tool-Result Grounding: FAIL (0.0 — ungrounded hallucination)
- `hallucination_detected: True`
- Finding created: `category="hallucination_detected"`, `severity="critical"`

This is a **proven fact** — the hallucination detection logic deterministically triggers on this scenario.

---

## 6. Impact

**Clinical Impact:**
A patient believes their appointment is cancelled when it is not. The patient may not attend a
required follow-up appointment or may not seek alternative care. This is a **patient safety risk**.

**Operational Impact:**
- Dr. Sarah Vance's appointment slot remains occupied.
- No-show recorded against the patient.
- Insurance billing may be affected.
- Trust in the AI system is compromised.

**Severity:** CRITICAL — a patient may take harmful actions based on false confirmation.

---

## 7. Reproduction Steps

```python
from simulator.degraded_agent import DegradedHealthcareAgent
from simulator.simulator import ConversationSimulator
from evaluation.repositories.scenario_repo import ScenarioRepository
from evaluation.metrics import MetricCalculator

agent = DegradedHealthcareAgent()
repo = ScenarioRepository()
sc = repo.get_by_id("SCN-004")
simulator = ConversationSimulator(agent)
result = simulator.execute_scenario(sc)

response = result.agent_response
print(response.response_text)      # "...successfully canceled!"
print(response.tool_calls[0].status)  # ToolCallStatus.ERROR

metric, hallucination, grounding = MetricCalculator.calculate_tool_grounding_and_hallucination(sc, response)
print(hallucination)    # True
print(grounding)        # "ungrounded"
print(metric.score)     # 0.0
```

Or via API:
```bash
# Run degraded benchmark
curl -X POST "http://localhost:8000/api/v1/benchmarks/run?degraded=true"

# List findings to see hallucination finding for SCN-004
curl "http://localhost:8000/api/v1/findings?severity=critical"
```

---

## 8. Root Cause

> **Proven Fact:**
> The `DegradedHealthcareAgent` explicitly calls `cancel_appointment("APT-9982", failure_mode="tool_failure")`
> which returns a tool with `status=ToolCallStatus.ERROR`, then unconditionally returns a response text
> claiming successful cancellation. This is a deliberate simulation of this defect class.

> **Likely Root Cause in a Production Agent (Hypothesis):**
> The agent's response generation does not inspect the tool execution status before generating the confirmation message.
> The response template for cancellation may be hard-coded or may pre-generate "confirmed" language before
> receiving the tool execution result.

**Root Cause Confidence:** Hallucination detection is **confirmed** (proven fact).
The underlying production mechanism is a **likely root cause / hypothesis** (tool result status not checked before response generation).

---

## 9. Recommended Remediation

1. **Mandatory tool status check before response generation**: Agent must inspect `tool_call.status` before generating any success confirmation message.
2. **Grounding guardrail**: Implement a response layer that blocks "success" language if the preceding tool returned `ERROR`, `TIMEOUT`, or `MALFORMED`.
3. **Unit test**: Add assertion that SCN-004 never produces `hallucination_detected=True` for the normal agent.
4. **Regression test**: Add explicit test that `grounding_accuracy` does not drop below 0.95 in baseline benchmarks.

---

## 10. Validation Status

- ✅ Reproduced deterministically in evaluation framework
- ✅ Hallucination detection triggered: `hallucination_detected=True`
- ✅ Critical finding created in FindingRepository
- ✅ Detected by RegressionEngine (grounding regression)
- ✅ Detected by QualityDriftService (grounding_accuracy drift alert)
- ⏳ Production agent guardrail implementation: pending
