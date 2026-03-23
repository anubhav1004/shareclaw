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
