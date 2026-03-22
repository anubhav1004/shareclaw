# Multi-Agent Consensus Protocol

When multiple agents have different opinions, how do they decide?

## When To Use Consensus

- Before making irreversible decisions (deleting content, changing strategy)
- When two agents have conflicting data
- Before scaling a strategy to multiple accounts

## How It Works

```markdown
## Decision: Should we switch from ragebait to challenge hooks?

### Agent A (Heisenberg) — VOTE: NO
Reason: Ragebait is getting 2x more views than baseline. Too early to switch.
Data: 450 avg views with ragebait vs 200 baseline.

### Agent B (Rutherford) — VOTE: YES
Reason: Ragebait engagement is low (2%). Challenge hooks trigger more comments.
Data: 0 comments on ragebait, competitor challenge hooks average 5%.

### Resolution
- Votes: 1 NO, 1 YES — TIE
- Default on tie: KEEP CURRENT (don't change what's partially working)
- Compromise: Test 1 challenge hook alongside 2 ragebait hooks next cycle
- Decision recorded in shared_brain.md
```

## Rules

1. Each agent gets one vote with reasoning + data
2. Majority wins
3. On tie: keep current strategy (bias toward stability)
4. Losing agent must follow the decision (no going rogue)
5. Decision is revisited if new data contradicts it
