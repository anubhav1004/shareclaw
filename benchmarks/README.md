# Benchmarks

Benchmarks should answer one question:

> Does a ShareClaw-style swarm actually improve faster than an ad-hoc swarm?

The flagship benchmark compares two strategies across repeated simulated launches:

- **Ad-hoc swarm**: changes things and reacts to local wins, but does not keep durable memory of failures
- **ShareClaw swarm**: tests one variable at a time, keeps winners, avoids repeated failures, and compounds learning

## Run It

```bash
python benchmarks/launch_swarm.py
```

Or customize the run:

```bash
python benchmarks/launch_swarm.py --trials 500 --cycles 12 --seed 7
```

Machine-readable output:

```bash
python benchmarks/launch_swarm.py --json
```

## What To Look For

- cycle-by-cycle improvement
- final average activated users/day
- hit rate for the target threshold
- absolute and relative advantage for the ShareClaw swarm

This benchmark is synthetic, but it is designed to reflect the core ShareClaw thesis:

- durable memory beats repeated forgetting
- disciplined experimentation beats ad-hoc iteration
- explicit winners and failures create compounding advantages
