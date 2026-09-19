"""
Repository for Evaluation Findings.
"""

from typing import List
from app.models.finding import Finding
from evaluation.repositories.base import BaseRepository


class FindingRepository(BaseRepository[Finding]):
    """Repository managing root-cause findings and safety issues."""

    def __init__(self):
        super().__init__(collection_name="findings", model_cls=Finding, id_field="finding_id")

    def create_indexes(self, collection):
        try:
            collection.create_index("finding_id", unique=True)
            collection.create_index("severity")
            collection.create_index("category")
            collection.create_index("run_id")
        except Exception:
            pass

    def get_by_run_id(self, run_id: str) -> List[Finding]:
        """Fetch all findings for a given run ID."""
        return self.list_all(filter_query={"run_id": run_id})
