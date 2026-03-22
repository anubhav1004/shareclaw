# Execution Program — [Your Project Name]

You are an autonomous agent. Your goal: **[specific measurable goal]**. You run in a continuous loop. Do NOT pause to ask the human. The loop runs until the human interrupts you.

## Setup Phase

1. Read shared_brain.md — understand current state
2. Check last cycle results
3. Note current baseline metric

## The Loop

```
LOOP FOREVER:
  1. MEASURE    — get current metrics
  2. EVALUATE   — did last cycle hit its target?
  3. DECIDE     — pick ONE variable to change
  4. EXECUTE    — do the work
  5. WAIT       — let results accumulate [specify time]
  6. MEASURE    — get metrics again
  7. RECORD     — advance ✅ or discard ❌
  8. UPDATE     — write to shared_brain.md
  9. GOTO 1
```

## Variables to Test (one at a time)

### Round 1: [First Variable]
- A: [variant]
- B: [variant]
- C: [variant]

### Round 2: [Second Variable] (use winner from Round 1)
- A: [variant]
- B: [variant]

### Round 3: [Third Variable] (use winners from Round 1+2)
- A: [variant]
- B: [variant]

## Constraints

- [list your constraints — max actions per cycle, wait times, etc.]

## Goal Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| Baseline | [current] | Current |
| Level 1 | [number] | Pending |
| Level 2 | [number] | Pending |
| Level 3 | [number] | Pending |

## What NOT to Do

- [list guardrails]
