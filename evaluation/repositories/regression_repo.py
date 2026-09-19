"""
Repository for Regression Results.
"""

from app.models.regression import RegressionResult
from evaluation.repositories.base import BaseRepository


class RegressionResultRepository(BaseRepository[RegressionResult]):
    """Repository managing regression comparison records."""

    def __init__(self):
        super().__init__(collection_name="regression_results", model_cls=RegressionResult, id_field="regression_id")

    def create_indexes(self, collection):
        try:
            collection.create_index("regression_id", unique=True)
            collection.create_index("run_id")
            collection.create_index("baseline_run_id")
        except Exception:
            pass
