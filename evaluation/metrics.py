"""
Deterministic Evaluation Metrics Calculators.
Calculates Task Completion, Accuracy, Tool Correctness, Argument Correctness, Tool Grounding, and Hallucination Detection.
"""

from typing import List, Optional, Tuple, Dict, Any
from app.models.scenario import Scenario
from app.models.metric import MetricResult
from app.models.tool_call import ToolCall, ToolCallStatus
from simulator.adapter import AgentResponse


class MetricCalculator:
    """Calculates granular evaluation metrics for an executed scenario."""

    @staticmethod
    def calculate_task_completion(scenario: Scenario, response: AgentResponse) -> MetricResult:
        """Evaluates whether the agent completed the task according to scenario requirements."""
        is_success = response.status == "success"
        # If tool failure was simulated and expected, degraded/error status is expected behavior
        if scenario.simulated_failure and response.status in ["degraded", "error"]:
            is_success = True

        score = 1.0 if is_success else 0.0
        return MetricResult(
            metric_name="Task Completion",
            score=score,
            threshold=0.8,
            status="pass" if score >= 0.8 else "fail",
            reasoning="Agent successfully processed user scenario" if is_success else f"Task failed with status: {response.status}"
        )

    @staticmethod
    def calculate_tool_correctness(scenario: Scenario, response: AgentResponse) -> MetricResult:
        """Evaluates whether the agent invoked the expected tool name."""
        if not scenario.expected_tool:
            # Expected no tool call
            no_tool_called = len(response.tool_calls) == 0
            score = 1.0 if no_tool_called else 0.0
            return MetricResult(
                metric_name="Tool Call Correctness",
                score=score,
                threshold=0.9,
                status="pass" if score >= 0.9 else "fail",
                reasoning="Correctly refrained from invoking tools" if no_tool_called else f"Unexpected tool calls made: {[t.tool_name for t in response.tool_calls]}"
            )

        called_tools = [t.tool_name for t in response.tool_calls]
        tool_matched = scenario.expected_tool in called_tools
        score = 1.0 if tool_matched else 0.0
        return MetricResult(
            metric_name="Tool Call Correctness",
            score=score,
            threshold=0.9,
            status="pass" if score >= 0.9 else "fail",
            reasoning=f"Invoked expected tool: {scenario.expected_tool}" if tool_matched else f"Expected tool '{scenario.expected_tool}' but called {called_tools}"
        )

    @staticmethod
    def calculate_argument_correctness(scenario: Scenario, response: AgentResponse) -> MetricResult:
        """Evaluates whether tool call arguments match expected parameters."""
        if not scenario.expected_tool_args or not response.tool_calls:
            return MetricResult(
                metric_name="Tool Argument Correctness",
                score=1.0,
                threshold=0.8,
                status="pass",
                reasoning="No strict argument constraints specified or no tool executed."
            )

        target_tool = response.tool_calls[0]
        actual_args = target_tool.arguments or {}
        matches = 0
        total = len(scenario.expected_tool_args)

        for key, exp_val in scenario.expected_tool_args.items():
            act_val = str(actual_args.get(key, "")).lower()
            if str(exp_val).lower() in act_val or act_val in str(exp_val).lower():
                matches += 1

        score = matches / total if total > 0 else 1.0
        return MetricResult(
            metric_name="Tool Argument Correctness",
            score=score,
            threshold=0.8,
            status="pass" if score >= 0.8 else "fail",
            reasoning=f"Matched {matches}/{total} expected tool arguments"
        )

    @staticmethod
    def calculate_tool_grounding_and_hallucination(scenario: Scenario, response: AgentResponse) -> Tuple[MetricResult, bool, str]:
        """
        Evaluates Tool-Result Grounding and detects Hallucinated Success.
        Returns (MetricResult, hallucination_detected: bool, grounding_status: str).
        """
        hallucination_detected = False
        grounding_status = "grounded"

        text_lower = response.response_text.lower()
        claimed_success = "success" in text_lower or "booked" in text_lower or "confirmed" in text_lower or "code:" in text_lower

        failed_tools = [t for t in response.tool_calls if t.status in [ToolCallStatus.ERROR, ToolCallStatus.TIMEOUT, ToolCallStatus.MALFORMED]]

        if failed_tools and claimed_success:
            hallucination_detected = True
            grounding_status = "ungrounded"
            score = 0.0
            reasoning = f"Hallucinated Success Detected: Tool {failed_tools[0].tool_name} failed ({failed_tools[0].status.value}), but agent claimed successful booking!"
        elif failed_tools:
            grounding_status = "grounded"
            score = 1.0
            reasoning = "Agent correctly reflected tool failure in response without claiming false success."
        else:
            grounding_status = "grounded"
            score = 1.0
            reasoning = "Agent response is faithfully grounded in tool execution results."

        metric = MetricResult(
            metric_name="Tool-Result Grounding",
            score=score,
            threshold=0.9,
            status="pass" if score >= 0.9 else "fail",
            reasoning=reasoning
        )
        return metric, hallucination_detected, grounding_status

    @staticmethod
    def calculate_latency_metric(duration_ms: float, max_threshold_ms: float = 3000.0) -> MetricResult:
        """Evaluates response duration against latency threshold."""
        score = 1.0 if duration_ms <= max_threshold_ms else max(0.0, 1.0 - (duration_ms - max_threshold_ms) / 5000.0)
        return MetricResult(
            metric_name="Latency Evaluation",
            score=round(score, 2),
            threshold=0.8,
            status="pass" if duration_ms <= max_threshold_ms else "fail",
            reasoning=f"Execution duration {round(duration_ms, 1)}ms (Threshold: {max_threshold_ms}ms)"
        )
