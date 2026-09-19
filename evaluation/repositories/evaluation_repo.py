"""
Repository for Evaluation Results.
"""

from typing import List
from app.models.evaluation import EvaluationResult
from evaluation.repositories.base import BaseRepository


class EvaluationResultRepository(BaseRepository[EvaluationResult]):
    """Repository managing individual EvaluationResults for scenario runs."""

    def __init__(self):
        super().__init__(collection_name="evaluations", model_cls=EvaluationResult, id_field="result_id")

    def create_indexes(self, collection):
        try:
            collection.create_index("result_id", unique=True)
            collection.create_index("run_id")
            collection.create_index("scenario_id")
            collection.create_index("status")
        except Exception:
            pass

    def get_by_run_id(self, run_id: str) -> List[EvaluationResult]:
        """Fetch all results for a given evaluation run."""
        return self.list_all(filter_query={"run_id": run_id})
