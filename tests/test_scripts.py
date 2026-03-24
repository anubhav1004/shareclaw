"""Smoke tests for runnable demo and benchmark scripts."""

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _env():
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    root = str(ROOT)
    env["PYTHONPATH"] = root if not existing else f"{root}{os.pathsep}{existing}"
    return env


def test_launch_swarm_demo_script(tmp_path):
    output_dir = tmp_path / "demo-output"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "launch-swarm" / "run_demo.py"),
            "--output-dir",
            str(output_dir),
            "--fresh",
        ],
        cwd=ROOT,
        env=_env(),
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Launch swarm demo complete." in result.stdout
    assert (output_dir / "launch_swarm_summary.json").exists()
    assert (output_dir / ".shareclaw" / "shared_brain.md").exists()
    assert (output_dir / ".shareclaw" / "task_queue.md").exists()
    assert (output_dir / ".shareclaw" / "decisions.md").exists()

    summary = json.loads((output_dir / "launch_swarm_summary.json").read_text())
    assert summary["completed_tasks"] >= 3
    assert summary["resolved_decisions"] >= 1


def test_launch_benchmark_script_json_output():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "benchmarks" / "launch_swarm.py"),
            "--trials",
            "12",
            "--cycles",
            "8",
            "--seed",
            "7",
            "--json",
        ],
        cwd=ROOT,
        env=_env(),
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["shareclaw_final_average"] > payload["ad_hoc_final_average"]
    assert len(payload["shareclaw_average_by_cycle"]) == 9


def test_bio_label_projection_bootstrap_script(tmp_path):
    output_dir = tmp_path / "bio-demo-output"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "bio-label-projection" / "bootstrap.py"),
            "--output-dir",
            str(output_dir),
            "--fresh",
        ],
        cwd=ROOT,
        env=_env(),
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Biology benchmark workspace created." in result.stdout
    assert (output_dir / "challenge_manifest.json").exists()
    assert (output_dir / "bootstrap_summary.json").exists()
    assert (output_dir / "winning_plan.json").exists()
    assert (output_dir / "winning_plan.md").exists()
    assert (output_dir / ".shareclaw" / "shared_brain.md").exists()

    manifest = json.loads((output_dir / "challenge_manifest.json").read_text())
    assert manifest["challenge_name"] == "Open Problems Label Projection"
    assert manifest["starter_dataset"]["name"] == "Zebrafish embryonic cells"

    winning_plan = json.loads((output_dir / "winning_plan.json").read_text())
    assert len(winning_plan["experiment_cycles"]) == 10
    assert winning_plan["method_stack"][0]["method_id"] == "pca_logistic_regression"


def test_bio_label_projection_baseline_dry_run(tmp_path):
    output_dir = tmp_path / "bio-demo-output"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "bio-label-projection" / "run_baseline.py"),
            "--workspace-dir",
            str(output_dir),
            "--dataset",
            "zebrafish",
            "--dry-run",
        ],
        cwd=ROOT,
        env=_env(),
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["dataset_key"] == "zebrafish"
    assert payload["feature_space"] == "pca"
    assert payload["model_name"] == "logistic_regression"


def test_bio_label_projection_baseline_dry_run_with_lda(tmp_path):
    output_dir = tmp_path / "bio-demo-output"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "bio-label-projection" / "run_baseline.py"),
            "--workspace-dir",
            str(output_dir),
            "--dataset",
            "zebrafish",
            "--model",
            "lda_lsqr_auto",
            "--dry-run",
        ],
        cwd=ROOT,
        env=_env(),
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["model_name"] == "lda_lsqr_auto"


def test_bio_label_projection_candidate_search_dry_run():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "bio-label-projection" / "search_task_candidates.py"),
            "--dry-run",
        ],
        cwd=ROOT,
        env=_env(),
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["count"] >= 10
    assert "logreg_balanced_c1" in payload["candidates"]
