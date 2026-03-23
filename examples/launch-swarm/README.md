# Launch Swarm

Turn a product launch into a self-improving system instead of a one-shot campaign.

## The Setup

Four agents share one ShareClaw workspace:

- **Research agent** finds hooks, competitors, and audience objections.
- **Builder agent** ships demos, landing pages, and onboarding changes.
- **Content agent** turns learnings into posts, clips, and threads.
- **Analytics agent** measures signups, activation, retention, and engagement.

All four agents read the same shared brain, pull tasks from the same queue, vote on big strategic changes, and publish events when something important happens.

## What They Optimize

- **North-star metric:** activated users per week
- **Supporting metrics:** GitHub stars, waitlist signups, demo conversion, day-1 activation
- **Variables:** hook, demo angle, CTA, landing page structure, proof style

## The Loop

1. Analytics agent updates the latest baseline.
2. Research agent proposes the next variable to test.
3. If the change is strategic, the swarm opens a consensus decision.
4. Builder and content agents pull tasks from the queue.
5. After launch, analytics agent records the result.
6. ShareClaw logs what worked, what failed, and the next target.

## Example Tasks

- [HIGH] Ship 45-second demo video with one killer use case
- [HIGH] Rewrite repo opening paragraph around “shared brain for agents”
- [MED] Test CTA: “Star the repo” vs “Run the swarm”
- [MED] Compare launch post framing: “agent memory” vs “self-improving system”

## Example Consensus Question

**Decision:** Should the launch center on “multi-agent memory” or “self-improving systems”?

- Builder: vote `SELF_IMPROVING_SYSTEMS` because it better captures the loop + coordination story
- Content: vote `SELF_IMPROVING_SYSTEMS` because it is more aspirational and memorable
- Analytics: vote `MULTI_AGENT_MEMORY` if early click-through says concrete framing converts better

## Why This Example Matters

This is the kind of system that can actually compound:

- learnings survive across launches
- failed tests are never forgotten
- agents stop duplicating work
- big decisions become explicit and reviewable
- the repo itself becomes the thing being optimized

That makes ShareClaw feel less like a helper utility and more like an operating system for ambitious agent teams.

## Run The Demo

```bash
python examples/launch-swarm/run_demo.py --fresh
```

This writes a real demo workspace to `examples/launch-swarm/.demo-output/` containing:

- `.shareclaw/brain.json`
- `.shareclaw/shared_brain.md`
- `.shareclaw/task_queue.md`
- `.shareclaw/decisions.md`
- `.shareclaw/events.md`
- `launch_swarm_summary.json`

The script exercises:

- target setting
- consensus and voting
- task queue pickup and completion
- handoffs
- events
- skill sharing
- learning, failures, introspection, and report generation
