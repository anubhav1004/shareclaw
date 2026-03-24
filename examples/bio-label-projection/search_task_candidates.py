#!/usr/bin/env python3
"""Search lightweight label projection candidates and log the sweep with ShareClaw."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = Path(__file__).resolve().parent
for path in (ROOT, EXAMPLE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from shareclaw import Brain

import bootstrap as bootstrap_module


def candidate_specs():
    """Return the candidate grid we want to search first."""
    return [
        {"id": "logreg_scaled_c0_5", "family": "logreg", "c": 0.5, "class_weight": None},
        {"id": "logreg_scaled_c1", "family": "logreg", "c": 1.0, "class_weight": None},
        {"id": "logreg_scaled_c2", "family": "logreg", "c": 2.0, "class_weight": None},
        {"id": "logreg_balanced_c0_25", "family": "logreg", "c": 0.25, "class_weight": "balanced"},
        {"id": "logreg_balanced_c0_5", "family": "logreg", "c": 0.5, "class_weight": "balanced"},
        {"id": "logreg_balanced_c1", "family": "logreg", "c": 1.0, "class_weight": "balanced"},
        {"id": "logreg_balanced_c2", "family": "logreg", "c": 2.0, "class_weight": "balanced"},
        {"id": "logreg_balanced_c4", "family": "logreg", "c": 4.0, "class_weight": "balanced"},
        {"id": "linear_svc_balanced_c0_25", "family": "linear_svc", "c": 0.25, "class_weight": "balanced"},
        {"id": "linear_svc_balanced_c0_5", "family": "linear_svc", "c": 0.5, "class_weight": "balanced"},
        {"id": "linear_svc_balanced_c1", "family": "linear_svc", "c": 1.0, "class_weight": "balanced"},
        {"id": "ridge_balanced_alpha0_1", "family": "ridge", "alpha": 0.1, "class_weight": "balanced"},
        {"id": "ridge_balanced_alpha1", "family": "ridge", "alpha": 1.0, "class_weight": "balanced"},
        {"id": "sgd_log_balanced_alpha1e_4", "family": "sgd", "alpha": 1e-4, "class_weight": "balanced"},
        {"id": "sgd_log_balanced_alpha1e_3", "family": "sgd", "alpha": 1e-3, "class_weight": "balanced"},
        {"id": "svc_rbf_balanced_c1", "family": "svc_rbf", "c": 1.0, "class_weight": "balanced"},
        {"id": "svc_rbf_balanced_c2", "family": "svc_rbf", "c": 2.0, "class_weight": "balanced"},
        {"id": "nearest_centroid", "family": "nearest_centroid"},
        {
            "id": "nearest_centroid_manhattan",
            "family": "nearest_centroid",
            "metric": "manhattan",
        },
        {
            "id": "nearest_centroid_shrink_0_05",
            "family": "nearest_centroid",
            "shrink_threshold": 0.05,
        },
        {
            "id": "nearest_centroid_shrink_0_1",
            "family": "nearest_centroid",
            "shrink_threshold": 0.1,
        },
        {
            "id": "nearest_centroid_shrink_0_25",
            "family": "nearest_centroid",
            "shrink_threshold": 0.25,
        },
        {
            "id": "nearest_centroid_shrink_0_5",
            "family": "nearest_centroid",
            "shrink_threshold": 0.5,
        },
        {"id": "lda_svd", "family": "lda", "solver": "svd"},
        {"id": "lda_lsqr_auto", "family": "lda", "solver": "lsqr", "shrinkage": "auto"},
        {"id": "qda_reg_0_01", "family": "qda", "reg_param": 0.01},
        {"id": "qda_reg_0_1", "family": "qda", "reg_param": 0.1},
        {"id": "qda_reg_0_25", "family": "qda", "reg_param": 0.25},
        {"id": "gaussian_nb", "family": "gaussian_nb"},
        {"id": "knn_distance_k1", "family": "knn", "n_neighbors": 1},
        {"id": "knn_distance_k3", "family": "knn", "n_neighbors": 3},
        {"id": "knn_distance_k5", "family": "knn", "n_neighbors": 5},
        {"id": "knn_distance_k9", "family": "knn", "n_neighbors": 9},
        {"id": "knn_distance_k15", "family": "knn", "n_neighbors": 15},
        {
            "id": "knn_uniform_k5",
            "family": "knn",
            "n_neighbors": 5,
            "weights": "uniform",
        },
        {
            "id": "knn_uniform_k15",
            "family": "knn",
            "n_neighbors": 15,
            "weights": "uniform",
        },
        {
            "id": "extra_trees_300",
            "family": "extra_trees",
            "n_estimators": 300,
            "class_weight": None,
        },
        {
            "id": "extra_trees_balanced_500",
            "family": "extra_trees",
            "n_estimators": 500,
            "class_weight": "balanced",
        },
        {
            "id": "random_forest_balanced_500",
            "family": "random_forest",
            "n_estimators": 500,
            "class_weight": "balanced_subsample",
        },
    ]


def _imports():
    try:
        import anndata as ad  # type: ignore
        import numpy as np  # type: ignore
        from sklearn.exceptions import ConvergenceWarning  # type: ignore
        from sklearn.discriminant_analysis import (  # type: ignore
            LinearDiscriminantAnalysis,
            QuadraticDiscriminantAnalysis,
        )
        from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier  # type: ignore
        from sklearn.linear_model import LogisticRegression, RidgeClassifier, SGDClassifier  # type: ignore
        from sklearn.metrics import accuracy_score, f1_score  # type: ignore
        from sklearn.naive_bayes import GaussianNB  # type: ignore
        from sklearn.neighbors import KNeighborsClassifier, NearestCentroid  # type: ignore
        from sklearn.pipeline import Pipeline  # type: ignore
        from sklearn.preprocessing import LabelEncoder, StandardScaler  # type: ignore
        from sklearn.svm import LinearSVC, SVC  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime guidance
        raise RuntimeError(
            "This search needs the biology example dependencies. "
            "Install them with: pip install -r examples/bio-label-projection/requirements.txt"
        ) from exc

    return {
        "ad": ad,
        "np": np,
        "ConvergenceWarning": ConvergenceWarning,
        "ExtraTreesClassifier": ExtraTreesClassifier,
        "GaussianNB": GaussianNB,
        "LinearDiscriminantAnalysis": LinearDiscriminantAnalysis,
        "LogisticRegression": LogisticRegression,
        "RidgeClassifier": RidgeClassifier,
        "QuadraticDiscriminantAnalysis": QuadraticDiscriminantAnalysis,
        "RandomForestClassifier": RandomForestClassifier,
        "SGDClassifier": SGDClassifier,
        "accuracy_score": accuracy_score,
        "f1_score": f1_score,
        "KNeighborsClassifier": KNeighborsClassifier,
        "NearestCentroid": NearestCentroid,
        "Pipeline": Pipeline,
        "LabelEncoder": LabelEncoder,
        "StandardScaler": StandardScaler,
        "LinearSVC": LinearSVC,
        "SVC": SVC,
    }


def build_model(spec: dict[str, object], libs):
    """Create a candidate model from a compact spec."""
    pipeline = libs["Pipeline"]
    scaler = libs["StandardScaler"]
    family = spec["family"]

    if family == "logreg":
        return pipeline(
            steps=[
                ("scale", scaler()),
                (
                    "model",
                    libs["LogisticRegression"](
                        C=float(spec["c"]),
                        max_iter=1000,
                        solver="lbfgs",
                        random_state=7,
                        class_weight=spec["class_weight"],
                    ),
                ),
            ]
        )
    if family == "linear_svc":
        return pipeline(
            steps=[
                ("scale", scaler()),
                (
                    "model",
                    libs["LinearSVC"](
                        C=float(spec["c"]),
                        class_weight=spec["class_weight"],
                        dual="auto",
                        random_state=7,
                        max_iter=10000,
                    ),
                ),
            ]
        )
    if family == "ridge":
        return pipeline(
            steps=[
                ("scale", scaler()),
                (
                    "model",
                    libs["RidgeClassifier"](
                        alpha=float(spec["alpha"]),
                        class_weight=spec["class_weight"],
                    ),
                ),
            ]
        )
    if family == "sgd":
        return pipeline(
            steps=[
                ("scale", scaler()),
                (
                    "model",
                    libs["SGDClassifier"](
                        loss="log_loss",
                        alpha=float(spec["alpha"]),
                        class_weight=spec["class_weight"],
                        max_iter=5000,
                        random_state=7,
                        tol=1e-4,
                    ),
                ),
            ]
        )
    if family == "svc_rbf":
        return pipeline(
            steps=[
                ("scale", scaler()),
                (
                    "model",
                    libs["SVC"](
                        C=float(spec["c"]),
                        kernel="rbf",
                        gamma="scale",
                        class_weight=spec["class_weight"],
                    ),
                ),
            ]
        )
    if family == "nearest_centroid":
        return pipeline(
            steps=[
                ("scale", scaler()),
                (
                    "model",
                    libs["NearestCentroid"](
                        metric=spec.get("metric", "euclidean"),
                        shrink_threshold=spec.get("shrink_threshold"),
                    ),
                ),
            ]
        )
    if family == "lda":
        return pipeline(
            steps=[
                ("scale", scaler()),
                (
                    "model",
                    libs["LinearDiscriminantAnalysis"](
                        solver=str(spec["solver"]),
                        shrinkage=spec.get("shrinkage"),
                    ),
                ),
            ]
        )
    if family == "qda":
        return pipeline(
            steps=[
                ("scale", scaler()),
                (
                    "model",
                    libs["QuadraticDiscriminantAnalysis"](
                        reg_param=float(spec["reg_param"]),
                    ),
                ),
            ]
        )
    if family == "gaussian_nb":
        return pipeline(
            steps=[
                ("scale", scaler()),
                ("model", libs["GaussianNB"]()),
            ]
        )
    if family == "knn":
        return pipeline(
            steps=[
                ("scale", scaler()),
                (
                    "model",
                    libs["KNeighborsClassifier"](
                        n_neighbors=int(spec["n_neighbors"]),
                        weights=str(spec.get("weights", "distance")),
                    ),
                ),
            ]
        )
    if family == "extra_trees":
        return libs["ExtraTreesClassifier"](
            n_estimators=int(spec["n_estimators"]),
            class_weight=spec["class_weight"],
            random_state=7,
            n_jobs=-1,
        )
    if family == "random_forest":
        return libs["RandomForestClassifier"](
            n_estimators=int(spec["n_estimators"]),
            class_weight=spec["class_weight"],
            random_state=7,
            n_jobs=-1,
        )

    raise ValueError(f"Unsupported family: {family}")


def dataset_paths(task_repo_dir: Path, names: list[str]):
    base = task_repo_dir / "resources_test" / "task_label_projection"
    return {
        name: {
            "train": base / name / "train.h5ad",
            "test": base / name / "test.h5ad",
            "solution": base / name / "solution.h5ad",
        }
        for name in names
    }


def evaluate_candidate(spec, datasets, libs):
    """Run one candidate across all datasets and return its scores."""
    ad = libs["ad"]
    encoder_cls = libs["LabelEncoder"]
    accuracy_score = libs["accuracy_score"]
    f1_score = libs["f1_score"]
    np = libs["np"]

    model = build_model(spec, libs)
    started = time.perf_counter()
    per_dataset = {}

    for name, paths in datasets.items():
        train = ad.read_h5ad(paths["train"])
        test = ad.read_h5ad(paths["test"])
        solution = ad.read_h5ad(paths["solution"])
        if "X_pca" not in train.obsm or "X_pca" not in test.obsm:
            raise KeyError(f"{name} is missing obsm['X_pca']")

        model.fit(train.obsm["X_pca"], train.obs["label"].astype(str))
        pred = model.predict(test.obsm["X_pca"])

        categories = list(solution.obs["label"].dtype.categories) + list(np.asarray(pred, dtype=str))
        encoder = encoder_cls().fit(categories)
        y_true = encoder.transform(solution.obs["label"])
        y_pred = encoder.transform(np.asarray(pred, dtype=str))

        per_dataset[name] = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
            "f1_weighted": float(f1_score(y_true, y_pred, average="weighted")),
            "n_obs": int(solution.n_obs),
        }

    elapsed = time.perf_counter() - started
    aggregate_macro = statistics.mean(item["f1_macro"] for item in per_dataset.values())
    aggregate_accuracy = statistics.mean(item["accuracy"] for item in per_dataset.values())
    aggregate_weighted = statistics.mean(item["f1_weighted"] for item in per_dataset.values())

    return {
        "id": spec["id"],
        "family": spec["family"],
        "params": {key: value for key, value in spec.items() if key not in {"id", "family"}},
        "aggregate_macro_f1": round(aggregate_macro, 6),
        "aggregate_accuracy": round(aggregate_accuracy, 6),
        "aggregate_weighted_f1": round(aggregate_weighted, 6),
        "elapsed_seconds": round(elapsed, 3),
        "datasets": per_dataset,
    }


def write_report(output_dir: Path, payload: dict[str, object]):
    leaderboard = payload["leaderboard"]
    lines = [
        "# Task Resource Candidate Search",
        "",
        f"- Primary score: `{payload['primary_score']}`",
        f"- Datasets: {', '.join(payload['datasets'])}",
        f"- Candidates tested: {payload['candidate_count']}",
        "",
        "## Top Candidates",
    ]
    for item in leaderboard[: min(10, len(leaderboard))]:
        lines.extend(
            [
                f"### {item['id']}",
                f"- aggregate_macro_f1: {item['aggregate_macro_f1']:.4f}",
                f"- aggregate_accuracy: {item['aggregate_accuracy']:.4f}",
                f"- aggregate_weighted_f1: {item['aggregate_weighted_f1']:.4f}",
                f"- elapsed_seconds: {item['elapsed_seconds']:.3f}",
                "",
            ]
        )

    (output_dir / "search_report.md").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def run_search(task_repo_dir: Path, workspace_dir: Path, dataset_names: list[str], top_k: int = 5):
    if not (workspace_dir / ".shareclaw" / "brain.json").exists():
        bootstrap_module.bootstrap(workspace_dir, fresh=False)

    libs = _imports()
    warnings.filterwarnings("ignore", category=libs["ConvergenceWarning"])
    datasets = dataset_paths(task_repo_dir, dataset_names)

    brain = Brain(
        "bio-task-search",
        path=str(workspace_dir / ".shareclaw"),
        objective="Find the strongest lightweight label projection candidate on official task resources.",
        metric="aggregate_macro_f1",
        variables=["candidate_method"],
        wait_time="1 search cycle",
        step_size=1.05,
    )
    brain.set_target("Increase aggregate_macro_f1 on official task resources and package only the winner.")

    output_dir = workspace_dir / "candidate-search"
    output_dir.mkdir(parents=True, exist_ok=True)

    leaderboard = []
    best = 0.0
    winner = None

    for spec in candidate_specs():
        try:
            result = evaluate_candidate(spec, datasets, libs)
        except Exception as exc:  # pragma: no cover - runtime exploration
            brain.fail(
                f"{spec['id']} failed during task-resource evaluation",
                reason=str(exc),
            )
            leaderboard.append(
                {
                    "id": spec["id"],
                    "family": spec["family"],
                    "error": str(exc),
                }
            )
            continue

        status = "advance" if result["aggregate_macro_f1"] > best else "discard"
        brain.log_cycle(
            "candidate_method",
            result["id"],
            round(best, 6),
            result["aggregate_macro_f1"],
            status,
            f"aggregate_accuracy={result['aggregate_accuracy']:.4f}; aggregate_weighted_f1={result['aggregate_weighted_f1']:.4f}",
        )
        if status == "advance":
            best = result["aggregate_macro_f1"]
            winner = result["id"]
            brain.learn(
                f"{result['id']} is the new leading lightweight candidate",
                evidence=(
                    f"aggregate_macro_f1={result['aggregate_macro_f1']:.4f}, "
                    f"aggregate_accuracy={result['aggregate_accuracy']:.4f}, "
                    f"aggregate_weighted_f1={result['aggregate_weighted_f1']:.4f}"
                ),
            )
        else:
            brain.fail(
                f"{result['id']} did not beat the current search leader",
                reason=f"aggregate_macro_f1={result['aggregate_macro_f1']:.4f} vs best={best:.4f}",
            )

        leaderboard.append(result)

    successful = [item for item in leaderboard if "aggregate_macro_f1" in item]
    successful.sort(
        key=lambda item: (
            item["aggregate_macro_f1"],
            item["aggregate_accuracy"],
            item["aggregate_weighted_f1"],
        ),
        reverse=True,
    )

    payload = {
        "primary_score": "aggregate_macro_f1",
        "datasets": dataset_names,
        "candidate_count": len(candidate_specs()),
        "leaderboard": successful,
        "winner": winner,
        "top_k": successful[:top_k],
        "failed": [item for item in leaderboard if "error" in item],
    }
    (output_dir / "leaderboard.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_report(output_dir, payload)
    brain.emit(
        "TASK_CANDIDATE_SEARCH_COMPLETED",
        {
            "winner": winner,
            "candidates": len(successful),
            "failed": len(payload["failed"]),
            "output_dir": str(output_dir),
        },
        agent="search",
        details="Completed a ShareClaw-logged sweep over official task resources.",
    )

    print(json.dumps(payload["top_k"], indent=2))
    return payload


def main():
    parser = argparse.ArgumentParser(
        description="Search task-resource candidate methods and log the sweep with ShareClaw."
    )
    parser.add_argument(
        "--task-repo-dir",
        required=False,
        default="",
        help="Path to the task_label_projection repository containing resources_test.",
    )
    parser.add_argument(
        "--workspace-dir",
        default=str(EXAMPLE_DIR / ".demo-output"),
        help="ShareClaw workspace directory for logging the search.",
    )
    parser.add_argument(
        "--dataset",
        dest="datasets",
        action="append",
        default=[],
        help="Dataset name under resources_test/task_label_projection/. Repeat to add multiple datasets.",
    )
    parser.add_argument("--top-k", type=int, default=5, help="How many leading candidates to print.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the candidate ids without importing scientific dependencies.",
    )
    args = parser.parse_args()

    if args.dry_run:
        payload = {
            "candidates": [item["id"] for item in candidate_specs()],
            "count": len(candidate_specs()),
        }
        print(json.dumps(payload, indent=2))
        return

    if not args.task_repo_dir:
        raise SystemExit("--task-repo-dir is required unless --dry-run is used.")

    datasets = args.datasets or ["cxg_immune_cell_atlas", "pancreas"]
    run_search(
        task_repo_dir=Path(args.task_repo_dir),
        workspace_dir=Path(args.workspace_dir),
        dataset_names=datasets,
        top_k=args.top_k,
    )


if __name__ == "__main__":
    main()
