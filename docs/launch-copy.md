# Launch Copy

Use this file when posting ShareClaw publicly.

## X Post

```text
I built an open-source framework for self-improving agent systems.

ShareClaw gives agents:
- a shared brain
- a task queue
- consensus
- events
- handoffs

The point isn't “more agents”.
It's building a system that learns across cycles.

It also ships with:
- a runnable launch-swarm demo
- a benchmark comparing ShareClaw vs an ad-hoc swarm
- zero runtime dependencies

Repo: https://github.com/anubhav1004/shareclaw
```

## X Thread

```text
1/ I built ShareClaw: an open-source framework for self-improving agent systems.

Not just agents doing tasks.
A system that remembers, coordinates, and improves across cycles.
```

```text
2/ The core idea:

Give your swarm:
- a shared brain
- a task queue
- explicit decisions
- an event stream
- handoffs

Then make it test one variable at a time and keep what works.
```

```text
3/ Most agent tooling optimizes orchestration inside one run.

ShareClaw optimizes what happens across runs:
- what the swarm learned
- what failed
- what it should try next
- what work is waiting
- what decisions are unresolved
```

```text
4/ I also added a runnable “launch swarm” demo.

It shows a team of agents coordinating a product launch:
- voting on positioning
- pulling tasks
- logging wins/failures
- converging on a better launch message
```

```text
5/ There’s also a small benchmark:

ShareClaw-style swarm vs ad-hoc swarm.

In the current synthetic benchmark run:
- ad-hoc final average: 50.93
- ShareClaw final average: 61.29
- relative advantage: +20.3%
```

```text
6/ The repo is zero-dependency at runtime, ships with markdown mirrors for humans + agents, and has 61 passing tests.

Repo: https://github.com/anubhav1004/shareclaw
```

## Hacker News

### Title

Show HN: ShareClaw, a shared brain + coordination layer for self-improving agent swarms

### Body

```text
I built ShareClaw, an open-source memory and coordination layer for multi-agent systems.

Most agent frameworks focus on orchestration inside one run. ShareClaw focuses on what the swarm remembers and improves across runs:

- shared brain for goals, wins, failures, cycles, and winning combinations
- task queue for shared work
- consensus for strategic decisions
- event stream for coordination
- handoffs between specialist agents
- one-variable-at-a-time learning loop

The runtime is JSON-backed with markdown mirrors, so both code and file-based agents can use it easily.

This release also includes:
- a runnable launch-swarm demo
- a benchmark comparing a ShareClaw-style swarm with an ad-hoc swarm
- zero runtime dependencies

Repo: https://github.com/anubhav1004/shareclaw
```

## GitHub Release Summary

### Title

`ShareClaw v0.2.0 — launch swarms, benchmarks, and real coordination primitives`

### Short Description

```text
ShareClaw v0.2.0 turns the project from a promising shared-memory utility into a much more complete self-improving agent system runtime.
```
