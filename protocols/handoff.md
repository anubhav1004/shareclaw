# Agent Handoff Protocol

How one agent cleanly passes work to another.

## The Problem

Agent A generates content. Agent B needs to analyze it. Without a protocol:
- Agent B doesn't know Agent A finished
- Agent B doesn't know where the output is
- Agent B re-does work Agent A already did

## The Solution: Handoff Files

When Agent A completes a task for Agent B, it writes a handoff file:

```markdown
# Handoff: content-generation → analysis

**From:** Agent A (Heisenberg)
**To:** Agent B (Rutherford)
**Timestamp:** 2026-03-21T14:00:00Z
**Status:** ready_for_review

## What Was Done
- Generated 3 TikTok videos with ragebait hooks
- Applied text overlay (HelveticaNeue 38px)
- Mixed Chopin audio at 30/70 ratio

## Output Files
- /output/video_01.mp4 (TAYLOR SWIFT hook)
- /output/video_02.mp4 (DUMBEST PERSON hook)
- /output/video_03.mp4 (teacher CHEATING hook)

## What Needs To Happen Next
- Schedule these to @sasha_glowingup via Postiz
- Space 5 hours apart, odd times
- Check analytics after 6 hours
- Write results to shared_brain.md

## Context From Shared Brain
- Current target: 500 views/post
- Using ragebait hook style (won cycle 1)
- Account was paused for 24h organic engagement
```

## Handoff States

```
created → ready_for_review → picked_up → in_progress → completed
                                                          ↓
                                                    → failed (with reason)
```

## Rules

1. Never start work on a handoff that's already `picked_up` by another agent
2. Always update the handoff state when you start and finish
3. If a handoff is `created` for more than 1 hour with no pickup, alert via Discord/Slack
