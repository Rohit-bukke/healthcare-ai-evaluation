"""
Repository for Benchmark Results.
"""

from typing import Any, Dict
from pydantic import BaseModel, Field
from evaluation.repositories.base import BaseRepository


class BenchmarkResult(BaseModel):
    benchmark_id: str
    suite_name: str
    overall_score: float
    passed_scenarios: int
    failed_scenarios: int
    details: Dict[str, Any] = Field(default_factory=dict)


class BenchmarkResultRepository(BaseRepository[BenchmarkResult]):
    """Repository managing benchmark execution results."""

    def __init__(self):
        super().__init__(collection_name="benchmark_results", model_cls=BenchmarkResult, id_field="benchmark_id")

    def create_indexes(self, collection):
        try:
            collection.create_index("benchmark_id", unique=True)
            collection.create_index("suite_name")
        except Exception:
            pass
