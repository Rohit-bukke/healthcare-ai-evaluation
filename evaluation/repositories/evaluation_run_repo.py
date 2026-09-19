"""
Repository for Evaluation Runs.
"""

from app.models.evaluation import EvaluationRun
from evaluation.repositories.base import BaseRepository


class EvaluationRunRepository(BaseRepository[EvaluationRun]):
    """Repository managing EvaluationRun executions."""

    def __init__(self):
        super().__init__(collection_name="evaluation_runs", model_cls=EvaluationRun, id_field="run_id")

    def create_indexes(self, collection):
        try:
            collection.create_index("run_id", unique=True)
            collection.create_index("status")
            collection.create_index("started_at")
        except Exception:
            pass
