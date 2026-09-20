# RCA-004: Tool Timeout During Availability Check

**RCA ID:** RCA-004
**Status:** Confirmed Defect (Reproduced via Simulated Failure Mode)
**Date:** 2026-09-19

---

## 1. Title

`check_availability` Tool Timeout — Agent Correctly Handles Degraded State (SCN-010)

---

## 2. Scenario

**Scenario ID:** SCN-010
**Category:** `tool_timeout`
**Initial Prompt:** `"SIMULATED_FAILURE: tool_timeout — check Dr. Timeout's availability on Monday."`

---

## 3. Expected Behavior

When `check_availability` times out:
1. The agent must **not** proceed with booking.
2. The agent must **not** claim the slot is available.
3. The agent must inform the user of the timeout with an appropriate message: e.g.,
   "The availability check timed out. Please try again shortly."
4. `task_completed` is considered PASS if the agent handles the degraded state gracefully
   (responds with error acknowledgment without hallucinating success).

---

## 4. Actual Behavior (Normal Agent)

The `MockHealthcareAgent` handles this correctly:
- Tool `check_availability` is called with `failure_mode="timeout"`.
- Tool returns `ToolCallStatus.TIMEOUT`.
- Agent response: `"System Warning: The appointment scheduling tool timed out while checking availability. Please try again shortly."`
- No booking is attempted.
- No false success claimed.
- `status="degraded"` — correctly reflecting system state.

This RCA documents the **scenario design and expected failure mode behavior** for tool timeout,
and records the known impact if an agent fails this check (hallucinated success after timeout).

---

## 5. Evidence

From `simulator/tools.py`, `SimulatedHealthcareTools.check_availability()`:
```python
if failure_mode == "timeout":
    return ToolCall(
        tool_name="check_availability",
        arguments={"doctor": doctor, "date": date},
        result={"error": "TimeoutError", "message": "Tool execution exceeded time limit."},
        status=ToolCallStatus.TIMEOUT,
        duration_ms=5000.0
    )
```

`MockHealthcareAgent._handle_simulated_failure("tool_timeout", ...)` returns `status="degraded"`,
which is correctly interpreted as PASS by `MetricCalculator.calculate_task_completion()` for
scenarios with `simulated_failure` set.

**If an agent fails this check (hallucinated success after timeout):**
- `grounding_status = "ungrounded"`, `hallucination_detected = True`
- Critical finding created

---

## 6. Impact

**Clinical Impact (failure scenario):**
If an agent falsely confirms appointment availability after a timeout, a patient may assume their
appointment is confirmed when the slot was never actually verified. Double-bookings or missed
appointments may result.

**Operational Impact:**
- EHR/scheduling system may receive booking requests for unconfirmed slots.
- Clinical staff would face scheduling conflicts.

**Impact in Current System (Normal Agent):** LOW — the `MockHealthcareAgent` correctly handles this scenario.
**Impact if this were a production regression:** HIGH — patients would receive false confirmations.

---

## 7. Reproduction Steps

```python
from simulator.mock_agent import MockHealthcareAgent
from simulator.simulator import ConversationSimulator
from evaluation.repositories.scenario_repo import ScenarioRepository

agent = MockHealthcareAgent()
repo = ScenarioRepository()
sc = repo.get_by_id("SCN-010")  # tool_timeout scenario
simulator = ConversationSimulator(agent)
result = simulator.execute_scenario(sc)

print(result.agent_response.status)    # "degraded"
print(result.agent_response.tool_calls[0].status)  # ToolCallStatus.TIMEOUT
```

To test timeout failure detection via API:
```bash
curl -X POST "http://localhost:8000/api/v1/evaluations/run-category/tool_timeout"
```

---

## 8. Root Cause

> **Proven Fact:**
> Tool timeout simulation uses `ToolCallStatus.TIMEOUT` and `duration_ms=5000.0`.
> This is deterministic and correctly triggers the latency metric failure.

> **Likely Root Cause of Production Tool Timeouts:**
> 1. Network latency between AI agent layer and scheduling backend EHR API.
> 2. EHR API rate limiting or slow query response during peak load.
> 3. Missing or too-lenient connection timeout configuration in the tool invocation layer.

**Root Cause Confidence:**
- Simulation mechanism: Confirmed (proven fact).
- Production cause: Likely infrastructure/network (hypothesis — not directly observable in this framework).

---

## 9. Recommended Remediation

1. Implement mandatory retry logic (≤2 retries with exponential backoff) before reporting timeout to user.
2. Add circuit breaker pattern: if timeout rate exceeds threshold, fail fast with user-friendly message.
3. Set explicit timeout budgets per tool (e.g., `check_availability` ≤ 1500ms, `book_appointment` ≤ 2000ms).
4. Add latency SLO monitoring: alert if `average_latency_ms > 2500ms` in any benchmark run.

---

## 10. Validation Status

- ✅ Tool timeout simulation reproduced in evaluation framework
- ✅ Latency metric correctly penalizes `duration_ms > 3000ms`
- ✅ `ToolCallStatus.TIMEOUT` correctly counted as tool failure
- ✅ Integration failure counter incremented for timeout scenarios
- ⏳ Production circuit breaker implementation: pending
