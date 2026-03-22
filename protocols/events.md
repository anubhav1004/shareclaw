# Agent Event System

Agents can publish events that other agents subscribe to.

## Event Format

Write events to `events.md` (append-only):

```markdown
## 2026-03-21T14:30:00Z — VIDEO_POSTED
**Agent:** heisenberg
**Details:** Posted 3 ragebait videos to @sasha_glowingup
**Data:** video_ids: [7619..., 7619..., 7619...]
**Subscribers should:** Check analytics in 6 hours

## 2026-03-21T20:30:00Z — ANALYTICS_READY
**Agent:** rutherford
**Details:** 6h analytics scraped for today's posts
**Data:** avg_views: 380, best: 450, worst: 280
**Subscribers should:** Update shared_brain.md with results

## 2026-03-21T21:00:00Z — TARGET_HIT
**Agent:** rutherford
**Details:** Video #1 crossed 500 views!
**Data:** video_id: 7619..., views: 520, likes: 15
**Subscribers should:** Celebrate. Update milestones. Plan next target.

## 2026-03-21T21:05:00Z — STRATEGY_UPDATED
**Agent:** rutherford
**Details:** Updated shared_brain.md — ragebait confirmed as winning hook style
**Subscribers should:** Read shared_brain.md before next action
```

## Event Types

| Event | Meaning | Who Should Care |
|-------|---------|----------------|
| `TASK_CREATED` | New task in queue | Any idle agent |
| `VIDEO_POSTED` | Content published | Analytics agents |
| `ANALYTICS_READY` | Metrics scraped | Strategy agents |
| `TARGET_HIT` | Milestone achieved | All agents |
| `TARGET_MISSED` | Cycle failed | Strategy agents |
| `STRATEGY_UPDATED` | Shared brain changed | All agents |
| `SKILL_CREATED` | New shared skill | All agents |
| `ALERT` | Something needs attention | Humans + all agents |
