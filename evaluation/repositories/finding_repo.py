"""
Repository for Evaluation Findings.
Supports filtering by severity, status, category, and run ID.
"""

from typing import List, Optional
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
            collection.create_index("status")
        except Exception:
            pass

    def get_by_run_id(self, run_id: str) -> List[Finding]:
        """Fetch all findings for a given run ID."""
        return self.list_all(filter_query={"run_id": run_id})

    def get_by_severity(self, severity: str) -> List[Finding]:
        """Fetch findings filtered by severity (critical, high, medium, low)."""
        return self.list_all(filter_query={"severity": severity})

    def get_by_status(self, status: str) -> List[Finding]:
        """Fetch findings filtered by status (open, under_investigation, remediated, etc)."""
        return self.list_all(filter_query={"status": status})

    def get_by_category(self, category: str) -> List[Finding]:
        """Fetch findings filtered by category."""
        return self.list_all(filter_query={"category": category})
