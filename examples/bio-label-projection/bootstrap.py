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


SOURCES = {
    "openproblems_home": "https://openproblems.bio/",
    "openproblems_benchmarks": "https://openproblems.bio/benchmarks",
    "task_structure": "https://openproblems.bio/documentation/reference/openproblems/src-task_id",
    "task_design_api": "https://openproblems.bio/documentation/create_task/design_api/",
    "zebrafish_dataset": "https://openproblems.bio/datasets/openproblems_v1/zebrafish",
    "gtex_v9_dataset": "https://openproblems.bio/datasets/cellxgene_census/gtex_v9",
    "immune_cell_atlas": "https://openproblems.bio/datasets/cellxgene_census/immune_cell_atlas",
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

    task_ids = [
        brain.create_task(
            "Download and inspect the official Zebrafish label projection dataset",
            priority="HIGH",
            details="Validate schema, labels, and train/test split assumptions against Open Problems conventions.",
            created_by="orchestrator",
        ),
        brain.create_task(
            "Implement a reproducible baseline label projection pipeline",
            priority="HIGH",
            details="Start with a simple baseline before trying more sophisticated methods.",
            created_by="orchestrator",
        ),
        brain.create_task(
            "Define the experiment table for preprocessing and classifier sweeps",
            priority="HIGH",
            details="Track one variable at a time: normalization, HVGs, PCA dims, classifier, calibration.",
            created_by="orchestrator",
        ),
        brain.create_task(
            "Add error analysis by cell type and confusion hotspots",
            priority="MED",
            details="The swarm should learn which cell types remain hard and why.",
            created_by="orchestrator",
        ),
        brain.create_task(
            "Plan scale-up from Zebrafish to GTEx v9 after the baseline stabilizes",
            priority="MED",
            details="Do not scale until the first benchmark run is reproducible.",
            created_by="orchestrator",
        ),
    ]

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

    brain.set_target("Establish a reproducible Zebrafish baseline with macro_f1 >= 0.75")
    brain.emit(
        "WORKSPACE_BOOTSTRAPPED",
        {"task_count": len(task_ids), "decision_id": decision_id},
        agent="orchestrator",
        details="Created a ShareClaw workspace for the first biology benchmark example.",
    )

    summary = {
        "files": brain.files(),
        "tasks": [task["title"] for task in brain.list_tasks(limit=10)],
        "decisions": [decision["question"] for decision in brain.list_decisions(limit=10)],
        "events": [event["type"] for event in brain.get_events(limit=10)],
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
