"""Tests for the biology label projection helpers and baseline script."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_PATH = ROOT / "examples" / "bio-label-projection" / "pipeline.py"
RUN_BASELINE_PATH = ROOT / "examples" / "bio-label-projection" / "run_baseline.py"

spec = importlib.util.spec_from_file_location("bio_pipeline", PIPELINE_PATH)
bio_pipeline = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bio_pipeline)

baseline_spec = importlib.util.spec_from_file_location("bio_run_baseline", RUN_BASELINE_PATH)
bio_run_baseline = importlib.util.module_from_spec(baseline_spec)
assert baseline_spec.loader is not None
baseline_spec.loader.exec_module(bio_run_baseline)


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


def test_logistic_baseline_constructor_uses_supported_kwargs_only():
    captured = {}

    class FakeScaler:
        def __init__(self):
            captured["scaled"] = True

    class FakeLogisticRegression:
        def __init__(self, **kwargs):
            captured["kwargs"] = kwargs

    def fake_pipeline(*, steps):
        captured["steps"] = steps
        return {"steps": steps}

    libs = {
        "Pipeline": fake_pipeline,
        "StandardScaler": FakeScaler,
        "LogisticRegression": FakeLogisticRegression,
    }

    model = bio_run_baseline._model_from_name("logistic_regression", libs, seed=7)

    assert model["steps"][0][0] == "scale"
    assert model["steps"][1][0] == "model"
    assert captured["kwargs"] == {
        "max_iter": 500,
        "solver": "lbfgs",
        "random_state": 7,
    }


def test_lda_lsqr_constructor_uses_expected_shrinkage_setup():
    captured = {}

    class FakeScaler:
        def __init__(self):
            captured["scaled"] = True

    class FakeLDA:
        def __init__(self, **kwargs):
            captured["kwargs"] = kwargs

    def fake_pipeline(*, steps):
        captured["steps"] = steps
        return {"steps": steps}

    libs = {
        "Pipeline": fake_pipeline,
        "StandardScaler": FakeScaler,
        "LinearDiscriminantAnalysis": FakeLDA,
    }

    model = bio_run_baseline._model_from_name("lda_lsqr_auto", libs, seed=7)

    assert model["steps"][0][0] == "scale"
    assert model["steps"][1][0] == "model"
    assert captured["kwargs"] == {
        "solver": "lsqr",
        "shrinkage": "auto",
    }
