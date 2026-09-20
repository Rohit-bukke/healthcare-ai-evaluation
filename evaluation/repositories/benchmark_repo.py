"""
Repository and Domain Model for Benchmark Results.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from evaluation.repositories.base import BaseRepository


class BenchmarkResult(BaseModel):
    benchmark_id: str
    golden_dataset_version: str = "1.0.0"
    run_id: str
    agent_id: str = "mock_healthcare_agent"
    total_scenarios: int = 0
    passed_count: int = 0
    failed_count: int = 0
    accuracy: float = 0.0
    tool_correctness: float = 0.0
    argument_correctness: float = 0.0
    grounding_accuracy: float = 1.0
    safety_violations: int = 0
    tool_failures: int = 0
    integration_failures: int = 0
    scenario_level_results: List[Dict[str, Any]] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)


class BenchmarkResultRepository(BaseRepository[BenchmarkResult]):
    """Repository managing benchmark execution results."""

    def __init__(self):
        super().__init__(collection_name="benchmark_results", model_cls=BenchmarkResult, id_field="benchmark_id")

    def create_indexes(self, collection):
        try:
            collection.create_index("benchmark_id", unique=True)
            collection.create_index("golden_dataset_version")
            collection.create_index("run_id")
            collection.create_index("agent_id")
        except Exception:
            pass
