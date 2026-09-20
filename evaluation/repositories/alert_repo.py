"""
Alert Repository for QualityDriftAlert persistence.
Uses the existing BaseRepository pattern (MongoDB + in-memory test fallback).
"""

from evaluation.repositories.base import BaseRepository
from app.models.alert import QualityDriftAlert


class AlertRepository(BaseRepository[QualityDriftAlert]):
    """Repository managing quality drift alert records."""

    def __init__(self):
        super().__init__(
            collection_name="quality_drift_alerts",
            model_cls=QualityDriftAlert,
            id_field="alert_id"
        )

    def create_indexes(self, collection):
        try:
            collection.create_index("alert_id", unique=True)
            collection.create_index("metric")
            collection.create_index("severity")
            collection.create_index("status")
            collection.create_index("benchmark_id")
            collection.create_index("created_at")
        except Exception:
            pass

    def get_by_status(self, status: str):
        """Retrieve alerts filtered by status (open, acknowledged, resolved)."""
        return self.list_all(filter_query={"status": status})

    def get_by_severity(self, severity: str):
        """Retrieve alerts filtered by severity."""
        return self.list_all(filter_query={"severity": severity})

    def get_by_benchmark(self, benchmark_id: str):
        """Retrieve all alerts triggered by a specific benchmark run."""
        return self.list_all(filter_query={"benchmark_id": benchmark_id})
