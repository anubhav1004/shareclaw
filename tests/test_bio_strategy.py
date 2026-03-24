"""Tests for the biology roadmap helpers."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRATEGY_PATH = ROOT / "examples" / "bio-label-projection" / "strategy.py"

spec = importlib.util.spec_from_file_location("bio_strategy", STRATEGY_PATH)
bio_strategy = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bio_strategy)


def test_roadmap_payload_has_ten_cycles_and_submission_steps():
    payload = bio_strategy.roadmap_payload("zebrafish")
    assert payload["challenge_name"] == "Open Problems Label Projection"
    assert payload["dataset_key"] == "zebrafish"
    assert len(payload["experiment_cycles"]) == 10
    assert len(payload["submission_checklist"]) >= 8


def test_method_stack_starts_with_trustworthy_lightweight_baselines():
    methods = bio_strategy.winning_method_stack()
    assert methods[0]["method_id"] == "pca_logistic_regression"
    assert methods[1]["method_id"] == "pca_knn_distance"
    assert methods[-1]["method_id"] == "calibrated_dual_head_ensemble"


def test_submission_checklist_mentions_viash_and_changelog():
    checklist = bio_strategy.submission_checklist()
    commands = " ".join(item["command"] for item in checklist)
    tasks = " ".join(item["task"] for item in checklist)
    assert "viash test" in commands
    assert "CHANGELOG.md" in tasks
