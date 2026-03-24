"""Helpers for the Open Problems label projection example."""

from __future__ import annotations

import csv
import json
import math
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


OFFICIAL_BUCKET_PREFIX = "https://openproblems-data.s3.amazonaws.com/resources/datasets"

DATASET_CATALOG = {
    "zebrafish": {
        "dataset_id": "openproblems_v1/zebrafish",
        "normalization_id": "l1_sqrt",
        "label_key": "cell_type",
        "group_key": "batch",
        "default_target": 0.75,
        "description": "Single-cell mRNA sequencing of zebrafish embryonic cells.",
    },
    "gtex_v9": {
        "dataset_id": "cellxgene_census/gtex_v9",
        "normalization_id": "l1_sqrt",
        "label_key": "cell_type",
        "group_key": "batch",
        "default_target": 0.60,
        "description": "GTEx v9 human tissues.",
    },
}


def official_dataset_url(dataset_id: str, normalization_id: str = "l1_sqrt") -> str:
    """Build the public HTTPS URL for an Open Problems common dataset."""
    dataset_id = dataset_id.strip("/")
    normalization_id = normalization_id.strip("/")
    return (
        f"{OFFICIAL_BUCKET_PREFIX}/{dataset_id}/{normalization_id}/dataset.h5ad"
    )


def resolve_dataset(dataset_name: str) -> Dict[str, str]:
    """Return official metadata for a named dataset shortcut."""
    if dataset_name not in DATASET_CATALOG:
        raise KeyError(f"Unknown dataset: {dataset_name}")
    record = dict(DATASET_CATALOG[dataset_name])
    record["dataset_url"] = official_dataset_url(
        record["dataset_id"], record["normalization_id"]
    )
    return record


def choose_split_strategy(num_groups: int) -> str:
    """Pick a reasonable evaluation split based on available batch groups."""
    return "group_shuffle" if num_groups >= 2 else "stratified_cells"


def shared_label_summary(
    train_labels: Sequence[str], test_labels: Sequence[str]
) -> Dict[str, List[str]]:
    """Summarize which labels are shared or missing across the split."""
    train_set = set(train_labels)
    test_set = set(test_labels)
    return {
        "shared": sorted(train_set & test_set),
        "train_only": sorted(train_set - test_set),
        "test_only": sorted(test_set - train_set),
    }


def format_metric_summary(metrics: Dict[str, float]) -> str:
    """Render compact metrics for logs and reports."""
    keys = ["macro_f1", "accuracy", "balanced_accuracy", "weighted_f1"]
    parts = []
    for key in keys:
        if key in metrics:
            parts.append(f"{key}={metrics[key]:.4f}")
    return ", ".join(parts)


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_predictions_csv(
    path: Path,
    rows: Iterable[Tuple[str, str, str, str]],
):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["cell_id", "true_label", "predicted_label", "group"])
        writer.writerows(rows)


def write_class_metrics_csv(path: Path, rows: Iterable[Dict[str, object]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        fieldnames = ["label", "precision", "recall", "f1", "support"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_report(path: Path, title: str, sections: List[Tuple[str, List[str]]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.append(f"## {heading}")
        lines.extend(body)
        lines.append("")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def download_file(url: str, destination: Path, chunk_size: int = 1024 * 1024) -> Path:
    """Download a file with stdlib only so the example stays lightweight."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "shareclaw/0.2.0"})
    with urllib.request.urlopen(request) as response, open(destination, "wb") as out:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out.write(chunk)
    return destination


def scientific_imports():
    """Import optional scientific dependencies only when needed."""
    try:
        import anndata  # type: ignore
        import numpy as np  # type: ignore
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis  # type: ignore
        from sklearn.linear_model import LogisticRegression  # type: ignore
        from sklearn.metrics import (  # type: ignore
            accuracy_score,
            balanced_accuracy_score,
            f1_score,
            precision_recall_fscore_support,
        )
        from sklearn.model_selection import GroupShuffleSplit, StratifiedShuffleSplit  # type: ignore
        from sklearn.neighbors import KNeighborsClassifier, NearestCentroid  # type: ignore
        from sklearn.pipeline import Pipeline  # type: ignore
        from sklearn.preprocessing import StandardScaler  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime guidance
        raise RuntimeError(
            "This biology example needs optional scientific Python packages. "
            "Install them with: pip install -r examples/bio-label-projection/requirements.txt"
        ) from exc

    return {
        "anndata": anndata,
        "np": np,
        "LinearDiscriminantAnalysis": LinearDiscriminantAnalysis,
        "LogisticRegression": LogisticRegression,
        "accuracy_score": accuracy_score,
        "balanced_accuracy_score": balanced_accuracy_score,
        "f1_score": f1_score,
        "precision_recall_fscore_support": precision_recall_fscore_support,
        "GroupShuffleSplit": GroupShuffleSplit,
        "StratifiedShuffleSplit": StratifiedShuffleSplit,
        "KNeighborsClassifier": KNeighborsClassifier,
        "NearestCentroid": NearestCentroid,
        "Pipeline": Pipeline,
        "StandardScaler": StandardScaler,
    }


def infer_previous_best(brain) -> float:
    """Read the current best metric from the ShareClaw brain if present."""
    winning = brain.winning_combo()
    best = 0.0
    for result in winning.values():
        value = result.get("value")
        if isinstance(value, (int, float)):
            best = max(best, float(value))
    if brain.state.get("history"):
        for item in brain.state["history"]:
            metric = item.get("metric")
            if isinstance(metric, (int, float)) and not math.isnan(metric):
                best = max(best, float(metric))
    return best
