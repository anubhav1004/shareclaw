"""Winning-plan helpers for the Open Problems label projection example."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


ROADMAP_LINKS = {
    "benchmarks": "https://openproblems.bio/benchmarks",
    "task_repo": "https://github.com/openproblems-bio/task_label_projection",
    "components_docs": "https://openproblems.bio/documentation/fundamentals/components",
    "getting_started": "https://openproblems.bio/documentation/create_component/getting_started",
    "add_method": "https://openproblems.bio/documentation/create_component/add_a_method",
    "create_pull_request": "https://openproblems.bio/documentation/create_component/create_pull_request",
}


def winning_method_stack() -> List[Dict[str, object]]:
    """Return the staged method progression we should test first."""
    return [
        {
            "rank": 1,
            "method_id": "pca_logistic_regression",
            "name": "Official PCA + logistic regression",
            "hypothesis": (
                "A leak-free linear baseline on the provided X_pca embedding is the fastest "
                "way to establish a trustworthy floor."
            ),
            "components": ["official X_pca", "StandardScaler", "LogisticRegression"],
            "promote_if": "Reproducible across seeds and clearly better than the current floor.",
            "drop_if": "Metrics move wildly across seeds or class breakdowns show severe rare-label collapse.",
        },
        {
            "rank": 2,
            "method_id": "pca_knn_distance",
            "name": "Official PCA + distance-weighted kNN",
            "hypothesis": (
                "Local neighborhoods may preserve fine-grained cell identity better than a single linear boundary."
            ),
            "components": ["official X_pca", "StandardScaler", "distance-weighted kNN"],
            "promote_if": "Macro F1 improves and confusion shrinks for closely related cell states.",
            "drop_if": "Memory cost rises with no measurable gain over the linear baseline.",
        },
        {
            "rank": 3,
            "method_id": "hvg_pca_balanced_linear",
            "name": "Recomputed HVG PCA + class-balanced linear head",
            "hypothesis": (
                "Rebuilding the representation from normalized counts and highly variable genes can recover "
                "signal that the generic embedding smooths away."
            ),
            "components": [
                "normalized counts",
                "highly variable genes",
                "PCA dimension sweep",
                "class-weighted LogisticRegression",
            ],
            "promote_if": "Rare and intermediate populations improve without hurting common classes.",
            "drop_if": "The representation is slower but does not beat the official PCA feature space.",
        },
        {
            "rank": 4,
            "method_id": "prototype_cosine_mapper",
            "name": "Class prototypes + cosine similarity",
            "hypothesis": (
                "Per-class centroids or prototypes can stabilize predictions for classes with coherent expression programs."
            ),
            "components": ["best embedding so far", "per-label prototypes", "cosine similarity", "neighbor smoothing"],
            "promote_if": "Confusion hotspots tighten and predictions stay stable under held-out batches.",
            "drop_if": "Prototype boundaries are too coarse for transitional cell states.",
        },
        {
            "rank": 5,
            "method_id": "batch_robust_latent_mapper",
            "name": "Batch-robust latent model + simple prediction head",
            "hypothesis": (
                "If lightweight methods plateau, a batch-aware latent space should improve transfer across held-out batches "
                "and make scale-up to GTEx more credible."
            ),
            "components": [
                "batch-robust latent model",
                "linear or prototype head",
                "strict held-out batch validation",
            ],
            "promote_if": "It beats the best lightweight method on Zebrafish and still transfers on GTEx.",
            "drop_if": "Infrastructure cost explodes without a clear gain over simpler methods.",
        },
        {
            "rank": 6,
            "method_id": "calibrated_dual_head_ensemble",
            "name": "Calibrated ensemble of best linear and prototype heads",
            "hypothesis": (
                "Once the top two heads are known, a small calibrated ensemble may lift overall rank without inventing a giant new model."
            ),
            "components": ["best linear head", "best prototype head", "probability calibration", "ensemble vote"],
            "promote_if": "The ensemble wins on both macro F1 and balanced accuracy.",
            "drop_if": "The ensemble is brittle or only improves on one dataset.",
        },
    ]


def experiment_cycles(dataset_key: str = "zebrafish") -> List[Dict[str, object]]:
    """Return a 10-cycle experiment table for a ShareClaw improvement loop."""
    return [
        {
            "cycle": 1,
            "title": f"Reproduce a leak-free {dataset_key} baseline",
            "focus": "reproducibility",
            "change": "Run the official PCA + logistic regression baseline end to end and save every artifact.",
            "success_gate": "A real run finishes, reports macro F1, and writes predictions, class metrics, and report files.",
            "advance_if_win": "Lock this in as the floor and never tune without comparing back to it.",
            "if_it_loses": "Fix the split, labels, or artifact logging before doing any model work.",
        },
        {
            "cycle": 2,
            "title": "Compare linear vs local classifiers on the same embedding",
            "focus": "model family",
            "change": "Compare logistic regression against distance-weighted kNN on official X_pca.",
            "success_gate": "One model beats the other by at least 0.01 macro F1 or clearly improves hard classes.",
            "advance_if_win": "Promote the winning head as the default lightweight baseline.",
            "if_it_loses": "Keep logistic regression as the default because it is cheaper and easier to package.",
        },
        {
            "cycle": 3,
            "title": "Recompute representation from normalized counts and HVGs",
            "focus": "feature selection",
            "change": "Add a new feature path using normalized counts, highly variable genes, and PCA.",
            "success_gate": "The best model on the recomputed representation beats the official PCA floor.",
            "advance_if_win": "Adopt the new representation for the next three cycles.",
            "if_it_loses": "Stay on official X_pca and avoid extra preprocessing complexity.",
        },
        {
            "cycle": 4,
            "title": "Sweep embedding dimensionality",
            "focus": "embedding dims",
            "change": "Evaluate a small PCA sweep such as 32, 64, 128, and 256 dimensions.",
            "success_gate": "Pick one dimension that improves macro F1 without hurting balanced accuracy.",
            "advance_if_win": "Freeze the best dimension and stop revisiting it unless the representation changes.",
            "if_it_loses": "Keep the smaller dimension that is fastest and most stable.",
        },
        {
            "cycle": 5,
            "title": "Protect rare labels with class balancing",
            "focus": "class imbalance",
            "change": "Add class weighting and report per-label movement for low-support cell types.",
            "success_gate": "Rare-label F1 improves without a large drop on common classes.",
            "advance_if_win": "Keep class balancing and document which labels it rescues.",
            "if_it_loses": "Remove class weighting and search for representation fixes instead.",
        },
        {
            "cycle": 6,
            "title": "Test prototype mapping in the best embedding",
            "focus": "decision rule",
            "change": "Build class prototypes and compare cosine-similarity mapping against the best linear head.",
            "success_gate": "Prototype mapping reduces confusion among related cell states or lifts macro F1.",
            "advance_if_win": "Carry both the linear head and prototype head into ensemble testing.",
            "if_it_loses": "Keep prototype mapping as a diagnostic tool only.",
        },
        {
            "cycle": 7,
            "title": "Try a small calibrated ensemble",
            "focus": "calibration",
            "change": "Blend the best linear and prototype heads and calibrate probabilities on the validation split.",
            "success_gate": "The ensemble beats the single best head on macro F1 and balanced accuracy.",
            "advance_if_win": "Use the ensemble as the current local champion.",
            "if_it_loses": "Prefer the simpler single-head winner for easier packaging.",
        },
        {
            "cycle": 8,
            "title": "Escalate only if lightweight methods plateau",
            "focus": "batch robustness",
            "change": "Introduce a batch-robust latent model only after the lightweight path has clearly plateaued.",
            "success_gate": "The batch-aware latent model wins on held-out batches and stays reproducible.",
            "advance_if_win": "Promote it as the candidate method for scale-up.",
            "if_it_loses": "Stay with the simpler champion and record why the heavy model did not justify itself.",
        },
        {
            "cycle": 9,
            "title": "Validate the winner on GTEx v9",
            "focus": "generalization",
            "change": "Run the best local champion on GTEx v9 before claiming we have a serious method.",
            "success_gate": "The method still clears a respectable score floor on GTEx and keeps the same failure profile story.",
            "advance_if_win": "Call the method submission-worthy and package it.",
            "if_it_loses": "Return to representation and batch-robustness work before packaging.",
        },
        {
            "cycle": 10,
            "title": "Package the champion as an Open Problems method",
            "focus": "submission",
            "change": "Implement the champion as a Viash component in the label_projection task repo and prepare the PR.",
            "success_gate": "The component passes local viash tests, runs on local files, and is documented in the changelog.",
            "advance_if_win": "Open the PR and start collecting reviewer feedback.",
            "if_it_loses": "Fix packaging gaps first; no benchmark bragging without a valid component.",
        },
    ]


def submission_checklist() -> List[Dict[str, str]]:
    """Return the concrete Open Problems submission checklist."""
    return [
        {
            "step": "1",
            "task": "Check the task repo issues, then fork and clone openproblems-bio/task_label_projection with submodules.",
            "command": "git clone --recursive <your-fork-url>",
        },
        {
            "step": "2",
            "task": "Sync the task repo with upstream main and download the test resources before editing components.",
            "command": "scripts/sync_resources.sh",
        },
        {
            "step": "3",
            "task": "Create a new method component with a unique snake_case method id and fill in the required metadata in config.vsh.yaml.",
            "command": "create_*_method.sh --name <method_name>",
        },
        {
            "step": "4",
            "task": "Implement the method script so it reads input train/test AnnData files and writes a valid prediction AnnData output.",
            "command": "viash run src/methods/<method_name>/config.vsh.yaml -- --input_train ... --input_test ... --output output.h5ad",
        },
        {
            "step": "5",
            "task": "Keep dependencies explicit in the component config and rebuild the container setup whenever dependencies change.",
            "command": "viash run src/methods/<method_name>/config.vsh.yaml -- ---setup cachedbuild",
        },
        {
            "step": "6",
            "task": "Run the component unit test from the API merge file and fix every schema or format error before submission.",
            "command": "viash test src/methods/<method_name>/config.vsh.yaml",
        },
        {
            "step": "7",
            "task": "Add a concise CHANGELOG.md entry describing the method and the benchmark impact it aims to improve.",
            "command": "edit CHANGELOG.md",
        },
        {
            "step": "8",
            "task": "Open the PR from your fork, compare across forks, and allow maintainer edits so reviewers can help land it.",
            "command": "Create PR on GitHub",
        },
    ]


def roadmap_payload(dataset_key: str = "zebrafish") -> Dict[str, object]:
    """Build the full competitive roadmap payload."""
    return {
        "challenge_name": "Open Problems Label Projection",
        "dataset_key": dataset_key,
        "win_definition": [
            "Build a leak-free local validation loop on Zebrafish.",
            "Beat the current local baseline with a method that stays interpretable and reproducible.",
            "Validate the champion on GTEx v9 before claiming transfer.",
            "Package the champion as a Viash method and open a pull request to the task repository.",
        ],
        "roadmap_links": ROADMAP_LINKS,
        "method_stack": winning_method_stack(),
        "experiment_cycles": experiment_cycles(dataset_key),
        "submission_checklist": submission_checklist(),
    }


def write_roadmap_json(path: Path, dataset_key: str = "zebrafish") -> Path:
    """Write the structured roadmap as JSON for agents to consume directly."""
    payload = roadmap_payload(dataset_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_roadmap_markdown(path: Path, dataset_key: str = "zebrafish") -> Path:
    """Write the roadmap as a human-readable markdown brief."""
    payload = roadmap_payload(dataset_key)
    lines = [
        "# Open Problems Label Projection Winning Plan",
        "",
        "## Win Definition",
    ]
    for item in payload["win_definition"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Source Links"])
    for name, url in payload["roadmap_links"].items():
        label = name.replace("_", " ").title()
        lines.append(f"- {label}: {url}")

    lines.extend(["", "## Method Stack"])
    for item in payload["method_stack"]:
        lines.extend(
            [
                f"### Stage {item['rank']}: {item['name']}",
                f"- Hypothesis: {item['hypothesis']}",
                f"- Components: {', '.join(item['components'])}",
                f"- Promote if: {item['promote_if']}",
                f"- Drop if: {item['drop_if']}",
                "",
            ]
        )

    lines.extend(["## Ten-Cycle Experiment Plan"])
    for cycle in payload["experiment_cycles"]:
        lines.extend(
            [
                f"### Cycle {cycle['cycle']}: {cycle['title']}",
                f"- Focus: {cycle['focus']}",
                f"- Change: {cycle['change']}",
                f"- Success gate: {cycle['success_gate']}",
                f"- Advance if win: {cycle['advance_if_win']}",
                f"- If it loses: {cycle['if_it_loses']}",
                "",
            ]
        )

    lines.extend(["## Submission Checklist"])
    for item in payload["submission_checklist"]:
        lines.append(f"{item['step']}. {item['task']} Command: `{item['command']}`")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return path
