"""
Scenario Repository with Git version-controlled YAML dataset loading support.
"""

import os
import yaml
import logging
from typing import List, Optional
from app.models.scenario import Scenario
from evaluation.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ScenarioRepository(BaseRepository[Scenario]):
    """Repository for managing Scenarios from Git YAML files and MongoDB."""

    def __init__(self, dataset_path: str = "datasets/reference_scenarios.yaml"):
        super().__init__(collection_name="scenarios", model_cls=Scenario, id_field="scenario_id")
        self.dataset_path = dataset_path
        self._load_from_git_dataset()

    def create_indexes(self, collection):
        """Create indexes on scenario_id and category."""
        try:
            collection.create_index("scenario_id", unique=True)
            collection.create_index("category")
        except Exception as err:
            logger.debug(f"Failed creating scenario indexes: {err}")

    def _load_from_git_dataset(self):
        """Loads version-controlled reference scenarios from YAML file into memory/DB."""
        if os.path.exists(self.dataset_path):
            try:
                with open(self.dataset_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "scenarios" in data:
                        for s_dict in data["scenarios"]:
                            scenario = Scenario.model_validate(s_dict)
                            self.insert(scenario)
                logger.info(f"Loaded {len(self._in_memory_store)} reference scenarios from {self.dataset_path}")
            except Exception as err:
                logger.error(f"Error loading reference dataset {self.dataset_path}: {err}")

    def get_by_category(self, category: str) -> List[Scenario]:
        """Fetch scenarios by category."""
        return self.list_all(filter_query={"category": category})
