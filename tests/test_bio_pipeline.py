"""Tests for the biology label projection helper module."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_PATH = ROOT / "examples" / "bio-label-projection" / "pipeline.py"

spec = importlib.util.spec_from_file_location("bio_pipeline", PIPELINE_PATH)
bio_pipeline = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bio_pipeline)


def test_official_dataset_url_uses_public_bucket():
    url = bio_pipeline.official_dataset_url("openproblems_v1/zebrafish", "l1_sqrt")
    assert (
        url
        == "https://openproblems-data.s3.amazonaws.com/resources/datasets/openproblems_v1/zebrafish/l1_sqrt/dataset.h5ad"
    )


def test_resolve_dataset_returns_verified_zebrafish_record():
    record = bio_pipeline.resolve_dataset("zebrafish")
    assert record["dataset_id"] == "openproblems_v1/zebrafish"
    assert record["label_key"] == "cell_type"
    assert record["group_key"] == "batch"
    assert record["dataset_url"].endswith("/openproblems_v1/zebrafish/l1_sqrt/dataset.h5ad")


def test_choose_split_strategy_prefers_group_split_when_possible():
    assert bio_pipeline.choose_split_strategy(1) == "stratified_cells"
    assert bio_pipeline.choose_split_strategy(2) == "group_shuffle"


def test_shared_label_summary_tracks_overlap_and_dropouts():
    summary = bio_pipeline.shared_label_summary(
        train_labels=["a", "b", "c"],
        test_labels=["b", "c", "d"],
    )
    assert summary["shared"] == ["b", "c"]
    assert summary["train_only"] == ["a"]
    assert summary["test_only"] == ["d"]
