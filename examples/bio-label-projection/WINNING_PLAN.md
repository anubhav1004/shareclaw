# Open Problems Label Projection Winning Plan

This is the concrete playbook for using ShareClaw to compete on the Open Problems label projection benchmark instead of just running one baseline and hoping.

## Win Definition

- build a leak-free local validation loop on Zebrafish
- beat the current local baseline with a method that stays interpretable and reproducible
- validate the champion on GTEx v9 before making strong claims
- package the champion as a Viash method and open a PR to `openproblems-bio/task_label_projection`

## Method Stack To Test First

### 1. Official PCA + logistic regression

- Why first: fastest trustworthy floor
- Components: official `X_pca`, scaling, `LogisticRegression`
- Promote when: it is stable across seeds and the per-class report looks sane

### 2. Official PCA + distance-weighted kNN

- Why next: checks whether local neighborhoods beat a single linear boundary
- Components: official `X_pca`, scaling, distance-weighted `KNeighborsClassifier`
- Promote when: hard neighboring cell states improve

### 3. HVG PCA + class-balanced linear head

- Why next: tests whether a recomputed representation from normalized counts carries stronger cell-type signal
- Components: normalized counts, highly variable genes, PCA sweep, class weighting
- Promote when: rare classes improve without collapsing common ones

### 4. Prototype cosine mapper

- Why next: some cell identities are better captured by class centroids than by a global decision boundary
- Components: best embedding so far, class prototypes, cosine similarity, optional neighbor smoothing
- Promote when: confusion hotspots tighten

### 5. Batch-robust latent mapper

- Why later: only bring heavier models in after the lightweight path plateaus
- Components: batch-aware latent space plus a simple prediction head
- Promote when: held-out batch transfer improves and the win survives on GTEx

### 6. Calibrated ensemble

- Why last: small ensembles can lift score after the best lightweight and best prototype heads are known
- Components: best linear head, best prototype head, calibration, ensemble vote
- Promote when: it wins on both macro F1 and balanced accuracy

## Ten-Cycle ShareClaw Experiment Plan

### Cycle 1

- Goal: reproduce a leak-free Zebrafish baseline
- Change: none, just establish the floor
- Success gate: a real run writes predictions, class metrics, and a report

### Cycle 2

- Goal: compare linear vs local classifiers
- Change: logistic regression vs distance-weighted kNN on the same embedding
- Success gate: at least one clear winner on macro F1 or hard classes

### Cycle 3

- Goal: test a recomputed representation
- Change: normalized counts + HVGs + PCA
- Success gate: beats the official PCA floor

### Cycle 4

- Goal: sweep embedding dimensionality
- Change: compare a small dimension grid like 32, 64, 128, 256
- Success gate: one stable best dimension

### Cycle 5

- Goal: protect rare classes
- Change: add class balancing and track per-label movement
- Success gate: rare-label F1 improves without a big common-class drop

### Cycle 6

- Goal: test prototype mapping
- Change: class prototypes plus cosine similarity in the best embedding
- Success gate: confusion hotspots improve

### Cycle 7

- Goal: try a small ensemble
- Change: blend the best linear and prototype heads
- Success gate: beats the single best head on macro F1 and balanced accuracy

### Cycle 8

- Goal: escalate only if the lightweight path plateaus
- Change: add a batch-robust latent model
- Success gate: wins on held-out batches and stays reproducible

### Cycle 9

- Goal: prove transfer
- Change: run the local champion on GTEx v9
- Success gate: the score and failure profile remain respectable

### Cycle 10

- Goal: submit
- Change: package the champion as a Viash method and prepare the PR
- Success gate: the component passes local tests and is changelog-ready

## Submission Checklist

1. Check `task_label_projection` issues, then fork and clone the repo with submodules.
2. Download the test resources with `scripts/sync_resources.sh`.
3. Create a new method component with a unique snake_case method id.
4. Fill in the required metadata in `config.vsh.yaml`.
5. Implement the script so it reads `input_train` and `input_test` and writes a valid prediction output.
6. Rebuild the component setup if dependencies change.
7. Run `viash test src/methods/<method_name>/config.vsh.yaml`.
8. Add a `CHANGELOG.md` entry.
9. Open the PR from your fork, compare across forks, and allow maintainer edits.

## Why ShareClaw Helps Here

The benchmark is ideal for a self-improving agent system because every cycle has:

- a measurable target
- a clean experiment variable
- explicit artifacts
- visible failure modes
- a contribution path that rewards reproducibility

That means the swarm can do real learning:

- preserve the best representation
- stop repeating failed model families
- track which labels remain hard
- decide when heavier infrastructure is justified
- package the winner for a real benchmark submission
