# Shared Task Queue

A shared task list that any agent can pick up and execute.

## Format: `task_queue.md`

```markdown
## Pending

- [ ] **[HIGH]** Check TikTok analytics for @sasha_glowingup — assigned: any — deadline: tonight
- [ ] **[MED]** Generate 3 new vlog montage videos — assigned: any — deadline: tomorrow
- [ ] **[LOW]** Refresh audio library with new trending sounds — assigned: any — deadline: this week

## In Progress

- [~] **[HIGH]** Post ragebait videos to TikTok — assigned: heisenberg — started: 2026-03-21T14:00

## Completed

- [x] **[HIGH]** Create ragebait hooks based on competitor research — completed: 2026-03-21T12:00 — by: claude-code — result: 3 hooks created, posted to Slack
- [x] **[MED]** Scrape StudyFetch top videos for hook inspiration — completed: 2026-03-21T10:00 — by: heisenberg — result: found 6.4M view hooks
```

## Rules

1. Any agent can add tasks
2. Any agent can pick up unassigned tasks
3. Mark `assigned: [your-name]` when you pick it up
4. Move to "Completed" with result when done
5. If stuck for 1 hour, move back to Pending with a note
6. HIGH priority tasks should be picked up within 30 minutes
