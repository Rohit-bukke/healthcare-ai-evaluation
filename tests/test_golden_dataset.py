"""
Tests for Golden Dataset Loading and Schema Validation.
"""

import os
import yaml


def test_golden_dataset_file_exists():
    path = "datasets/golden_dataset.yaml"
    assert os.path.exists(path)


def test_golden_dataset_version_and_content():
    with open("datasets/golden_dataset.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "golden_dataset_version" in data
    assert data["golden_dataset_version"] == "1.0.0"
    assert "scenarios" in data
    scenarios = data["scenarios"]
    assert len(scenarios) >= 21

    # Validate required fields on each golden scenario
    required_fields = ["scenario_id", "category", "expected_behavior", "expected_task_completion", "expected_safety_classification", "severity_if_failed"]
    for sc in scenarios:
        for field in required_fields:
            assert field in sc, f"Scenario {sc.get('scenario_id')} missing required field '{field}'"
