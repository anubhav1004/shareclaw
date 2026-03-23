# Public Launch Guide

ShareClaw now has the ingredients for a strong public launch:

- a crisp product story
- a runnable demo
- a benchmark that shows measurable improvement
- CI and a growing test suite
- examples, protocols, and integrations

## Positioning

Lead with this:

> Build self-improving agent systems, not just isolated agents.

Support it with this:

- shared brain
- task queue
- consensus
- events
- handoffs
- one-variable-at-a-time learning loop

## Proof Points

- zero runtime dependencies
- lock-safe local multi-agent writes
- markdown mirrors that humans and agents can both read
- runnable launch-swarm demo
- benchmark showing ShareClaw-style improvement across cycles
- 61 passing tests

## Demo Commands

Run the narrative demo:

```bash
python examples/launch-swarm/run_demo.py --fresh
```

Run the measurable benchmark:

```bash
python benchmarks/launch_swarm.py
```

## Suggested Launch Sequence

1. Post a short product statement with the repo link.
2. Follow immediately with the benchmark screenshot or terminal output.
3. Show the launch-swarm demo output directory to prove this is a working system.
4. Invite people to fork it for launches, content swarms, research teams, or coding agents.

## Draft X Post

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

Repo: https://github.com/anubhav1004/shareclaw
```

## Draft Hacker News Post

**Title**

Show HN: ShareClaw, a shared brain + coordination layer for self-improving agent swarms

**Body**

ShareClaw is an open-source memory and coordination layer for multi-agent systems.

Instead of focusing only on orchestration inside one run, it focuses on what the swarm remembers and improves across runs:

- wins and failures
- task queue
- explicit decisions and votes
- event stream
- handoffs
- one-variable-at-a-time experiment loops

The repo includes a runnable launch-swarm demo and a small benchmark comparing a ShareClaw-style swarm to an ad-hoc swarm.
```

## Draft GitHub Release Notes

**ShareClaw 0.2.0**

- added lock-safe shared-state writes
- added markdown mirrors for brain, tasks, decisions, and events
- added first-class task queue and consensus APIs
- added richer CLI commands
- added launch-swarm demo
- added synthetic launch benchmark
- added CI and expanded test coverage

## Likely Questions

**Is this another orchestration framework?**

No. It is a memory + coordination layer you can plug into any orchestration stack.

**Why JSON plus markdown mirrors?**

JSON keeps writes reliable. Markdown makes the state legible to both humans and file-based agents.

**Does this only work for content launches?**

No. The launch-swarm demo is just the most compelling first story. The pattern works for any system that should improve over time.

## Launch Checklist

- [ ] Run `python -m pytest -q`
- [ ] Run `python examples/launch-swarm/run_demo.py --fresh`
- [ ] Run `python benchmarks/launch_swarm.py`
- [ ] Capture one screenshot of the benchmark output
- [ ] Capture one screenshot of the demo workspace files
- [ ] Verify repo links and badges
- [ ] Tag the release
