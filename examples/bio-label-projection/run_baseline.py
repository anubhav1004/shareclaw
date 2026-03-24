#!/usr/bin/env python3
"""Run a reproducible baseline for Open Problems label projection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = Path(__file__).resolve().parent
for path in (ROOT, EXAMPLE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from shareclaw import Brain

import bootstrap as bootstrap_module
from pipeline import (
    choose_split_strategy,
    DATASET_CATALOG,
    download_file,
    format_metric_summary,
    infer_previous_best,
    official_dataset_url,
    resolve_dataset,
    scientific_imports,
    shared_label_summary,
    write_class_metrics_csv,
    write_json,
    write_markdown_report,
    write_predictions_csv,
)


def _model_from_name(model_name: str, libs, seed: int):
    if model_name == "logistic_regression":
        return libs["Pipeline"](
            steps=[
                ("scale", libs["StandardScaler"]()),
                (
                    "model",
                    libs["LogisticRegression"](
                        max_iter=500,
                        solver="lbfgs",
                        random_state=seed,
                    ),
                ),
            ]
        )
    if model_name == "knn":
        return libs["Pipeline"](
            steps=[
                ("scale", libs["StandardScaler"]()),
                ("model", libs["KNeighborsClassifier"](n_neighbors=15, weights="distance")),
            ]
        )
    if model_name == "lda_svd":
        return libs["Pipeline"](
            steps=[
                ("scale", libs["StandardScaler"]()),
                ("model", libs["LinearDiscriminantAnalysis"](solver="svd")),
            ]
        )
    if model_name == "lda_lsqr_auto":
        return libs["Pipeline"](
            steps=[
                ("scale", libs["StandardScaler"]()),
                (
                    "model",
                    libs["LinearDiscriminantAnalysis"](solver="lsqr", shrinkage="auto"),
                ),
            ]
        )
    if model_name == "nearest_centroid":
        return libs["Pipeline"](
            steps=[
                ("scale", libs["StandardScaler"]()),
                ("model", libs["NearestCentroid"]()),
            ]
        )
    if model_name == "nearest_centroid_shrink_0_1":
        return libs["Pipeline"](
            steps=[
                ("scale", libs["StandardScaler"]()),
                ("model", libs["NearestCentroid"](shrink_threshold=0.1)),
            ]
        )
    raise ValueError(f"Unsupported model: {model_name}")


def _load_feature_matrix(adata, feature_space: str, libs, max_cells: int | None, seed: int):
    np = libs["np"]
    total_cells = adata.n_obs
    indices = np.arange(total_cells)
    if max_cells and total_cells > max_cells:
        rng = np.random.default_rng(seed)
        indices = np.sort(rng.choice(indices, size=max_cells, replace=False))

    if feature_space == "pca":
        if "X_pca" not in adata.obsm:
            raise ValueError("Dataset does not contain obsm['X_pca']; choose a different feature space.")
        features = np.asarray(adata.obsm["X_pca"][indices], dtype=np.float32)
    else:
        raise ValueError("This first baseline currently supports feature_space='pca' only.")

    obs = adata.obs.iloc[indices].copy()
    return indices, features, obs


def _make_split(labels, groups, train_fraction: float, seed: int, libs):
    np = libs["np"]
    group_count = len(set(groups))
    strategy = choose_split_strategy(group_count)

    if strategy == "group_shuffle":
        splitter = libs["GroupShuffleSplit"](
            n_splits=1, train_size=train_fraction, random_state=seed
        )
        train_idx, test_idx = next(splitter.split(np.zeros(len(labels)), labels, groups))
    else:
        splitter = libs["StratifiedShuffleSplit"](
            n_splits=1, train_size=train_fraction, random_state=seed
        )
        train_idx, test_idx = next(splitter.split(np.zeros(len(labels)), labels))

    return strategy, train_idx, test_idx


def _filter_to_shared_labels(features, labels, groups, train_idx, test_idx):
    train_labels = [labels[idx] for idx in train_idx]
    test_labels = [labels[idx] for idx in test_idx]
    summary = shared_label_summary(train_labels, test_labels)
    allowed = set(summary["shared"])

    train_idx = [idx for idx in train_idx if labels[idx] in allowed]
    test_idx = [idx for idx in test_idx if labels[idx] in allowed]

    return (
        features[train_idx],
        features[test_idx],
        [labels[idx] for idx in train_idx],
        [labels[idx] for idx in test_idx],
        [groups[idx] for idx in test_idx],
        test_idx,
        summary,
    )


def run_baseline(
    workspace_dir: Path,
    dataset_key: str,
    dataset_path: Path | None = None,
    dataset_url: str | None = None,
    download_if_missing: bool = False,
    feature_space: str = "pca",
    model_name: str = "logistic_regression",
    train_fraction: float = 0.7,
    max_cells: int | None = None,
    seed: int = 7,
    dry_run: bool = False,
):
    record = resolve_dataset(dataset_key)
    dataset_url = dataset_url or record["dataset_url"]
    dataset_path = dataset_path or (workspace_dir / "data" / f"{dataset_key}.h5ad")

    if dry_run:
        plan = {
            "workspace_dir": str(workspace_dir),
            "dataset_key": dataset_key,
            "dataset_path": str(dataset_path),
            "dataset_url": dataset_url,
            "feature_space": feature_space,
            "model_name": model_name,
            "train_fraction": train_fraction,
            "max_cells": max_cells,
            "seed": seed,
        }
        print(json.dumps(plan, indent=2))
        return plan

    if not (workspace_dir / ".shareclaw" / "brain.json").exists():
        bootstrap_module.bootstrap(workspace_dir, fresh=False)

    if download_if_missing and not dataset_path.exists():
        print(f"Downloading dataset to {dataset_path} ...")
        download_file(dataset_url, dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {dataset_path}. "
            f"Download it first with: python examples/bio-label-projection/download_dataset.py --dataset {dataset_key}"
        )

    libs = scientific_imports()
    anndata = libs["anndata"]
    np = libs["np"]

    adata = anndata.read_h5ad(dataset_path, backed="r")
    index_subset, features, obs = _load_feature_matrix(
        adata, feature_space=feature_space, libs=libs, max_cells=max_cells, seed=seed
    )
    labels = obs[record["label_key"]].astype(str).tolist()
    groups = obs[record["group_key"]].astype(str).tolist()
    cell_ids = [str(index) for index in obs.index.tolist()]

    split_strategy, train_idx, test_idx = _make_split(labels, groups, train_fraction, seed, libs)
    (
        x_train,
        x_test,
        y_train,
        y_test,
        test_groups,
        filtered_test_idx,
        label_summary,
    ) = _filter_to_shared_labels(features, labels, groups, train_idx, test_idx)

    if not y_train or not y_test:
        raise RuntimeError("Split produced no overlapping labels between train and test.")

    model = _model_from_name(model_name, libs, seed)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    metrics = {
        "macro_f1": float(libs["f1_score"](y_test, predictions, average="macro")),
        "weighted_f1": float(libs["f1_score"](y_test, predictions, average="weighted")),
        "accuracy": float(libs["accuracy_score"](y_test, predictions)),
        "balanced_accuracy": float(
            libs["balanced_accuracy_score"](y_test, predictions)
        ),
    }

    labels_for_report = sorted(set(y_test) | set(predictions))
    precision, recall, f1, support = libs["precision_recall_fscore_support"](
        y_test, predictions, labels=labels_for_report, zero_division=0
    )
    class_rows = []
    for idx, label in enumerate(labels_for_report):
        class_rows.append(
            {
                "label": label,
                "precision": round(float(precision[idx]), 6),
                "recall": round(float(recall[idx]), 6),
                "f1": round(float(f1[idx]), 6),
                "support": int(support[idx]),
            }
        )

    results_dir = workspace_dir / "results" / f"{dataset_key}-{model_name}-{feature_space}"
    results_dir.mkdir(parents=True, exist_ok=True)

    write_json(
        results_dir / "metrics.json",
        {
            "dataset_key": dataset_key,
            "dataset_path": str(dataset_path),
            "dataset_url": dataset_url,
            "split_strategy": split_strategy,
            "train_fraction": train_fraction,
            "feature_space": feature_space,
            "model_name": model_name,
            "seed": seed,
            "subset_size": int(len(index_subset)),
            "train_cells": int(len(y_train)),
            "test_cells": int(len(y_test)),
            "label_summary": label_summary,
            "metrics": metrics,
        },
    )
    write_class_metrics_csv(results_dir / "class_metrics.csv", class_rows)
    write_predictions_csv(
        results_dir / "predictions.csv",
        (
            (cell_ids[filtered_test_idx[pos]], y_test[pos], str(predictions[pos]), test_groups[pos])
            for pos in range(len(y_test))
        ),
    )
    write_markdown_report(
        results_dir / "report.md",
        "Zebrafish Label Projection Baseline",
        [
            (
                "Run",
                [
                    f"- Dataset: {record['dataset_id']}",
                    f"- Local path: `{dataset_path}`",
                    f"- Feature space: `{feature_space}`",
                    f"- Model: `{model_name}`",
                    f"- Split strategy: `{split_strategy}`",
                    f"- Train fraction: {train_fraction}",
                    f"- Seed: {seed}",
                ],
            ),
            (
                "Metrics",
                [f"- {format_metric_summary(metrics)}"],
            ),
            (
                "Label Coverage",
                [
                    f"- shared labels: {len(label_summary['shared'])}",
                    f"- train-only labels dropped from evaluation: {len(label_summary['train_only'])}",
                    f"- test-only labels dropped from evaluation: {len(label_summary['test_only'])}",
                ],
            ),
        ],
    )

    brain = Brain("bio-label-projection-swarm", path=str(workspace_dir / ".shareclaw"))
    previous_best = infer_previous_best(brain)
    status = "advance" if metrics["macro_f1"] > previous_best else "discard"
    brain.log_cycle(
        "classifier_family",
        f"{model_name}+{feature_space}",
        round(previous_best, 4),
        round(metrics["macro_f1"], 4),
        status,
        f"{dataset_key} baseline with {split_strategy} split",
    )

    evidence = (
        f"{dataset_key} macro_f1={metrics['macro_f1']:.4f}, "
        f"accuracy={metrics['accuracy']:.4f}, balanced_accuracy={metrics['balanced_accuracy']:.4f}"
    )
    if status == "advance":
        brain.learn(
            f"{model_name} on {feature_space} features establishes a stronger {dataset_key} baseline",
            evidence=evidence,
        )
    else:
        brain.fail(
            f"{model_name} on {feature_space} features did not beat the current best baseline",
            reason=evidence,
        )

    brain.introspect(
        expected=f"Reach macro_f1 >= {record['default_target']:.2f} on {dataset_key}",
        actual=f"Observed macro_f1 = {metrics['macro_f1']:.4f}",
        why=(
            f"Split strategy was {split_strategy}; shared label count was {len(label_summary['shared'])}; "
            f"feature space was {feature_space}"
        ),
        next_action=(
            "Compare lda_svd, lda_lsqr_auto, and nearest_centroid against logistic_regression, "
            "then sweep PCA dimensions and batch-aware splits."
        ),
        next_target=f"Increase macro_f1 to at least {max(metrics['macro_f1'] + 0.03, record['default_target']):.2f}",
    )
    brain.emit(
        "BIO_BASELINE_COMPLETED",
        {
            "dataset": dataset_key,
            "model": model_name,
            "feature_space": feature_space,
            "macro_f1": round(metrics["macro_f1"], 6),
            "results_dir": str(results_dir),
        },
        agent="biology",
        details="Completed a reproducible label projection baseline run.",
    )

    task_title = "Implement a reproducible baseline label projection pipeline"
    matching = [task for task in brain.list_tasks(status="pending") if task["title"] == task_title]
    if matching:
        picked = brain.pickup_task("biology", matching[0]["id"])
        brain.complete_task(
            picked["id"],
            f"Baseline completed at macro_f1={metrics['macro_f1']:.4f}; results stored in {results_dir}",
            completed_by="biology",
        )

    print("Baseline run complete.")
    print(f"Results directory: {results_dir}")
    print(format_metric_summary(metrics))
    return {
        "metrics": metrics,
        "results_dir": str(results_dir),
        "dataset_path": str(dataset_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run a reproducible Open Problems label projection baseline."
    )
    parser.add_argument(
        "--workspace-dir",
        default=str(EXAMPLE_DIR / ".demo-output"),
        help="ShareClaw workspace directory for the biology example.",
    )
    parser.add_argument(
        "--dataset",
        default="zebrafish",
        choices=sorted(DATASET_CATALOG.keys()),
        help="Named dataset shortcut.",
    )
    parser.add_argument("--dataset-path", help="Local path to the .h5ad file.")
    parser.add_argument(
        "--dataset-url",
        help="Override the official download URL for the dataset.",
    )
    parser.add_argument(
        "--download-if-missing",
        action="store_true",
        help="Download the dataset automatically if it is missing locally.",
    )
    parser.add_argument(
        "--feature-space",
        default="pca",
        choices=["pca"],
        help="Feature representation to use for the baseline.",
    )
    parser.add_argument(
        "--model",
        default="logistic_regression",
        choices=[
            "logistic_regression",
            "knn",
            "lda_svd",
            "lda_lsqr_auto",
            "nearest_centroid",
            "nearest_centroid_shrink_0_1",
        ],
        help="Baseline classifier.",
    )
    parser.add_argument(
        "--train-fraction",
        type=float,
        default=0.7,
        help="Fraction of the split assigned to the reference/train partition.",
    )
    parser.add_argument(
        "--max-cells",
        type=int,
        default=None,
        help="Optional cap for faster local experiments.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved run plan without touching data or dependencies.",
    )
    args = parser.parse_args()

    run_baseline(
        workspace_dir=Path(args.workspace_dir),
        dataset_key=args.dataset,
        dataset_path=Path(args.dataset_path) if args.dataset_path else None,
        dataset_url=args.dataset_url,
        download_if_missing=args.download_if_missing,
        feature_space=args.feature_space,
        model_name=args.model,
        train_fraction=args.train_fraction,
        max_cells=args.max_cells,
        seed=args.seed,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
