#!/usr/bin/env python3
"""Bootstrap a ShareClaw workspace for a real biology benchmark."""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shareclaw import Brain
from strategy import ROADMAP_LINKS, roadmap_payload, write_roadmap_json, write_roadmap_markdown


SOURCES = {
    "openproblems_home": "https://openproblems.bio/",
    "openproblems_benchmarks": "https://openproblems.bio/benchmarks",
    "task_structure": "https://openproblems.bio/documentation/reference/openproblems/src-task_id",
    "task_design_api": "https://openproblems.bio/documentation/create_task/design_api/",
    "zebrafish_dataset": "https://openproblems.bio/datasets/openproblems_v1/zebrafish",
    "gtex_v9_dataset": "https://openproblems.bio/datasets/cellxgene_census/gtex_v9",
    "immune_cell_atlas": "https://openproblems.bio/datasets/cellxgene_census/immune_cell_atlas",
    "components_docs": ROADMAP_LINKS["components_docs"],
    "getting_started": ROADMAP_LINKS["getting_started"],
    "add_method": ROADMAP_LINKS["add_method"],
    "create_pull_request": ROADMAP_LINKS["create_pull_request"],
    "task_repo": ROADMAP_LINKS["task_repo"],
}


def bootstrap(output_dir: Path, fresh: bool = False):
    if fresh and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    brain = Brain(
        "bio-label-projection-swarm",
        path=str(output_dir / ".shareclaw"),
        objective="Build a reproducible, self-improving workflow for single-cell label projection on public Open Problems datasets.",
        metric="macro_f1",
        variables=[
            "normalization_strategy",
            "feature_selection",
            "embedding_dims",
            "classifier_family",
            "prediction_calibration",
        ],
        wait_time="1 experiment cycle",
        step_size=1.1,
    )

    manifest = {
        "challenge_name": "Open Problems Label Projection",
        "task": "Automated cell type annotation from rich, labeled reference data",
        "primary_metric": "macro_f1",
        "starter_dataset": {
            "name": "Zebrafish embryonic cells",
            "why": "smallest useful official label-projection dataset for fast iteration",
            "size": {
                "cells": 26022,
                "genes": 25258,
                "reported_size": "777.92 MiB",
            },
        },
        "scale_up_datasets": [
            {
                "name": "GTEx v9",
                "reported_size": "2.99 GiB",
                "cells": 209126,
                "genes": 28094,
            },
            {
                "name": "Immune Cell Atlas",
                "reported_size": "9.7 GiB",
                "cells": 329762,
                "genes": 29335,
            },
        ],
        "sources": SOURCES,
    }
    (output_dir / "challenge_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    roadmap = roadmap_payload("zebrafish")
    write_roadmap_json(output_dir / "winning_plan.json", dataset_key="zebrafish")
    write_roadmap_markdown(output_dir / "winning_plan.md", dataset_key="zebrafish")

    brain.emit(
        "BIO_CHALLENGE_SELECTED",
        {
            "challenge": manifest["challenge_name"],
            "starter_dataset": manifest["starter_dataset"]["name"],
        },
        agent="orchestrator",
        details="Selected a real biology benchmark with public data and leaderboards.",
    )

    decision_id = brain.start_consensus(
        "Should the first working example use Zebrafish rather than GTEx v9?",
        options=["ZEBRAFISH_FIRST", "GTEX_FIRST"],
        created_by="orchestrator",
        context=(
            "We want the first biology example to prove the loop works quickly before scaling "
            "to heavier cross-tissue datasets."
        ),
    )
    brain.vote(
        decision_id,
        agent="biology",
        choice="ZEBRAFISH_FIRST",
        reason="The developmental dataset is biologically meaningful and small enough for fast iteration.",
        data="Official page reports 26,022 cells x 25,258 genes.",
        confidence=0.87,
    )
    brain.vote(
        decision_id,
        agent="infra",
        choice="ZEBRAFISH_FIRST",
        reason="Smaller data keeps the first end-to-end example reproducible on normal hardware.",
        data="Official page reports 777.92 MiB.",
        confidence=0.92,
    )
    brain.vote(
        decision_id,
        agent="ambition",
        choice="GTEX_FIRST",
        reason="GTEx is more impressive for launch positioning because it is multi-tissue human data.",
        data="Official GTEx page reports 209,126 cells across tissues.",
        confidence=0.58,
    )
    brain.resolve_consensus(decision_id, resolved_by="orchestrator")

    second_decision_id = brain.start_consensus(
        "When should the swarm escalate from lightweight baselines to a batch-robust latent model?",
        options=["AFTER_LIGHTWEIGHT_PLATEAU", "IMMEDIATELY"],
        created_by="orchestrator",
        context=(
            "Heavy models may help transfer across batches, but they should not crowd out simpler "
            "baselines unless the lightweight path has clearly plateaued."
        ),
    )
    brain.vote(
        second_decision_id,
        agent="biology",
        choice="AFTER_LIGHTWEIGHT_PLATEAU",
        reason="We learn more from a disciplined baseline ladder than from jumping straight to heavy models.",
        data="The challenge rewards reproducibility as much as novelty.",
        confidence=0.9,
    )
    brain.vote(
        second_decision_id,
        agent="infra",
        choice="AFTER_LIGHTWEIGHT_PLATEAU",
        reason="The heavier path is justified only after simpler methods stop improving.",
        data="This keeps iteration fast and packaging easier.",
        confidence=0.94,
    )
    brain.vote(
        second_decision_id,
        agent="ambition",
        choice="IMMEDIATELY",
        reason="A batch-aware latent space may look more novel to reviewers and readers.",
        data="Novelty is useful, but only after a trustworthy floor exists.",
        confidence=0.52,
    )
    brain.resolve_consensus(second_decision_id, resolved_by="orchestrator")

    task_ids = []
    for cycle in roadmap["experiment_cycles"]:
        priority = "HIGH" if cycle["cycle"] <= 6 else "MED"
        details = (
            f"Focus: {cycle['focus']}\n"
            f"Change: {cycle['change']}\n"
            f"Success gate: {cycle['success_gate']}\n"
            f"Advance if win: {cycle['advance_if_win']}\n"
            f"If it loses: {cycle['if_it_loses']}"
        )
        task_ids.append(
            brain.create_task(
                f"Cycle {cycle['cycle']}: {cycle['title']}",
                priority=priority,
                details=details,
                created_by="orchestrator",
            )
        )

    brain.add_skill(
        "single-cell-error-analysis",
        description="Investigate failures by cell type, class imbalance, marker overlap, and domain shift rather than only reading the top-line score.",
        formula="score review + per-class breakdown + likely biological confounders",
        examples_good=[
            "Macrophages confuse with monocytes when marker sets overlap.",
            "Rare developmental populations fail due to class imbalance.",
        ],
        examples_bad=[
            "Only report the overall score.",
            "Scale up to larger datasets without understanding per-class failures.",
        ],
        code="focus on per-cell-type precision/recall before changing model family",
        created_by="biology",
    )
    brain.add_skill(
        "benchmark-discipline",
        description="Protect the benchmark from leakage and only promote methods that win with saved artifacts and reproducible validation.",
        formula="leak-free split + one variable changed + full artifact logging + cross-dataset check before bragging",
        examples_good=[
            "Compare two heads on the same embedding and keep the artifacts.",
            "Scale from Zebrafish to GTEx only after the local champion is stable.",
        ],
        examples_bad=[
            "Tune directly against the hidden solution.",
            "Change representation, model, and calibration all in the same cycle.",
        ],
        code="never claim a win without predictions.csv, metrics.json, class_metrics.csv, and report.md",
        created_by="orchestrator",
    )

    brain.set_target(
        "Establish a reproducible Zebrafish baseline, improve it methodically, validate on GTEx, and package a PR-ready Open Problems method."
    )
    brain.emit(
        "WORKSPACE_BOOTSTRAPPED",
        {
            "task_count": len(task_ids),
            "decision_ids": [decision_id, second_decision_id],
            "winning_plan": "winning_plan.json",
        },
        agent="orchestrator",
        details="Created a ShareClaw workspace with a competitive roadmap for the biology benchmark example.",
    )
    brain.emit(
        "WINNING_PLAN_SEEDED",
        {
            "method_stages": len(roadmap["method_stack"]),
            "experiment_cycles": len(roadmap["experiment_cycles"]),
            "submission_steps": len(roadmap["submission_checklist"]),
        },
        agent="orchestrator",
        details="Seeded the workspace with a staged method roadmap, experiment table, and submission checklist.",
    )

    summary = {
        "files": brain.files(),
        "tasks": [task["title"] for task in brain.list_tasks(limit=10)],
        "decisions": [decision["question"] for decision in brain.list_decisions(limit=10)],
        "events": [event["type"] for event in brain.get_events(limit=10)],
        "winning_plan": {
            "method_stages": len(roadmap["method_stack"]),
            "experiment_cycles": len(roadmap["experiment_cycles"]),
            "submission_steps": len(roadmap["submission_checklist"]),
        },
    }
    (output_dir / "bootstrap_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print("Biology benchmark workspace created.")
    print(f"Output directory: {output_dir}")
    print("Key files:")
    for name, path in brain.files().items():
        print(f"  - {name}: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap a ShareClaw workspace for the Open Problems label projection task."
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / ".demo-output"),
        help="Where the example workspace should be written.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete the existing output directory before bootstrapping.",
    )
    args = parser.parse_args()
    bootstrap(Path(args.output_dir), fresh=args.fresh)


if __name__ == "__main__":
    main()
