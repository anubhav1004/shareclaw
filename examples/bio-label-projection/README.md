# Bio Label Projection Swarm

This example turns a real biology benchmark into a ShareClaw workspace.

## Why This Challenge

If we want a biology example that is both credible and buildable, this is the one I would choose first:

- **Challenge family:** Open Problems in Single-Cell Analysis
- **Task:** Label projection
- **Problem statement:** automated cell type annotation from rich, labeled reference data

Why this is a strong first biology example:

- the benchmark is official and public
- the datasets are standardized and ready to use
- the task is mathematically clear
- the platform has continuous leaderboards
- there are multiple datasets, from manageable to large

In other words, it is exactly the kind of environment where a self-improving multi-agent system can prove its value.

## Dataset Strategy

I would start with the smallest useful official dataset and scale only after the workflow is stable.

### Phase 1

- **Dataset:** Zebrafish embryonic cells
- **Why first:** small enough to iterate on quickly
- **Official size:** 26,022 cells × 25,258 genes

### Phase 2

- **Dataset:** GTEx v9
- **Why next:** harder, multi-tissue, stronger biological signal

### Phase 3

- **Dataset:** Immune Cell Atlas
- **Why later:** very compelling biologically, but heavier

## What The Swarm Does

Agents coordinate on:

- choosing the first dataset
- defining the train/test evaluation plan
- building a reproducible baseline
- optimizing preprocessing and feature selection
- comparing model families
- analyzing failure modes by cell type
- deciding when to scale from Zebrafish to GTEx

## Run The Bootstrap

```bash
python examples/bio-label-projection/bootstrap.py --fresh
```

This creates a ShareClaw workspace in `examples/bio-label-projection/.demo-output/` with:

- source links and challenge metadata
- initial targets
- queue items
- a consensus decision
- recommended next experiments

## Why This Is Better Than Jumping Straight To Drug Response

An even flashier task would be perturbation prediction, but label projection is the better first proof:

- simpler and faster to iterate on
- less infra heavy
- easier to verify locally
- still biologically serious

Once this example works well, the natural phase 2 is perturbation prediction.
