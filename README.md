# 🧠 ShareClaw

**Shared memory and self-improving loops for multi-agent AI systems.**

Give your AI agents a shared brain. They read it before acting, write to it after acting, set targets, measure results, and get smarter every cycle.

> Built for [OpenClaw](https://openclaw.ai) agents. Works with any LLM agent system.

---

## The Problem

You have multiple AI agents (Heisenberg, Rutherford, Claude Code instances, GPT agents). Each one:
- Forgets what the other learned
- Repeats the same mistakes
- Has no shared context
- Can't set goals or track progress
- Doesn't know what worked and what didn't

## The Solution

**ShareClaw** is a protocol + template system for multi-agent shared memory:

```
Agent A reads shared_brain.md → acts → writes results back
                                                    ↓
Agent B reads shared_brain.md → sees what A learned → builds on it
                                                    ↓
Agent A reads again → sees B's results → next iteration
```

---

## Core Concepts

### 1. Shared Brain (`shared_brain.md`)

A living markdown file that ALL agents read and write to. Contains:

- **Current Target** — what we're trying to achieve right now (specific number)
- **What Works** — proven strategies (only added after data confirms)
- **What Doesn't Work** — failed approaches (never delete, only append)
- **Performance History** — metrics over time
- **Cycle Log** — each iteration with introspection
- **Next Plan** — conditional: "if X worked → do Y, if not → do Z"

```markdown
## Current Target
Cycle: 3
Target: Get avg engagement above 5% (currently 2.8%)
Variable being tested: Caption style — question format vs statement
Deadline: Check results by 2026-03-25

## What We Know Works
1. Ragebait hooks get 2x more views than motivational hooks — confirmed cycle 1 vs cycle 2
2. Posting at odd times (not :00) avoids bot detection — confirmed
3. 4 hashtags > 12 hashtags — data from competitor analysis

## What We Know Doesn't Work
1. Long 8-line text overlays — 200 views avg (cycle 1)
2. Mentioning product in first 2 lines — looks like an ad (cycle 2)
```

### 2. Execution Program (`execution.md`)

The autonomous loop program — like [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) but for any task.

```
LOOP FOREVER:
  1. Read shared_brain.md
  2. MEASURE current metrics
  3. EVALUATE — did last cycle hit target?
  4. DECIDE — change ONE variable
  5. EXECUTE — do the thing
  6. WAIT — let results accumulate
  7. MEASURE again
  8. RECORD — advance ✅ or discard ❌
  9. UPDATE shared_brain.md
  10. GOTO 1
```

**Key rules:**
- Only change ONE variable per cycle
- Always have a specific numeric target
- Keep what works, discard what doesn't
- Never pause to ask human — loop runs until interrupted

### 3. Introspection Protocol

Every cycle, agents answer 5 questions in the shared brain:

1. **What did we expect?** (hypothesis before executing)
2. **What actually happened?** (data after measuring)
3. **Why do we think it happened?** (analysis)
4. **What should we try next?** (decision)
5. **What is the specific target for next cycle?** (number)

This forces agents to think critically instead of blindly repeating.

### 4. Execution Log (`execution_log.tsv`)

Append-only log tracking every cycle:

```tsv
cycle  timestamp  variable_tested  variant  metric_before  metric_after  status  description
1  2026-03-21T12:00  hook_style  ragebait  200  450  advance  ragebait 2x better than motivational
2  2026-03-21T18:00  hook_style  challenge  200  180  discard  challenge format underperformed
3  2026-03-22T06:00  format  vlog_montage  450  600  advance  vlog format + ragebait = best combo
```

---

## How to Use

### Step 1: Create your shared brain

Copy `templates/shared_brain.md` to your workspace:

```bash
cp templates/shared_brain.md /path/to/workspace/shared_brain.md
```

Edit the sections for your use case.

### Step 2: Tell your agents about it

Add to each agent's system prompt / config:

```
SHARED BRAIN: Read /path/to/workspace/shared_brain.md BEFORE every task.
Write results AFTER every task. This file is shared between all agents.
Follow the introspection protocol. Set specific numeric targets.
```

### Step 3: Create your execution program

Copy `templates/execution.md` and customize the loop for your task:

```bash
cp templates/execution.md /path/to/workspace/execution.md
```

Define your variables to test, constraints, and goal milestones.

### Step 4: Let it run

Agents will read the shared brain, execute, measure, introspect, and update. Each cycle builds on the last. Over time, the system converges on what works.

---

## Templates

| File | Purpose |
|------|---------|
| [`templates/shared_brain.md`](templates/shared_brain.md) | Shared state template — customize for your use case |
| [`templates/execution.md`](templates/execution.md) | Autonomous loop program template |
| [`templates/execution_log.tsv`](templates/execution_log.tsv) | Cycle tracking log header |

## Examples

| Example | Use Case | Description |
|---------|----------|-------------|
| [`examples/tiktok-growth/`](examples/tiktok-growth/) | Social media growth | Autonomous TikTok content optimization — hooks, formats, audio, posting times |
| [`examples/content-pipeline/`](examples/content-pipeline/) | Content creation | Multi-agent content generation with quality iteration |

---

## Why This Works

Traditional AI agent systems are **stateless between sessions**. Each conversation starts fresh. ShareClaw makes agents **stateful across sessions and across agents**:

| Without ShareClaw | With ShareClaw |
|-------------------|----------------|
| Each agent starts fresh | Agents inherit all learnings |
| Same mistakes repeated | Mistakes logged, never repeated |
| No goals or targets | Specific numeric targets each cycle |
| Can't improve over time | Measurable improvement every cycle |
| Single agent works alone | Multiple agents collaborate on shared state |
| Human must direct everything | Agents self-direct using the loop |

---

## Real Results

Built and tested for TikTok + Instagram growth for an AI education app:

- Started: 200 views/post average
- After 3 cycles of the loop: identified ragebait hooks as 2x better
- After competitor analysis: discovered 4-hashtag strategy from 6M+ view videos
- Shared brain enabled Heisenberg (posts content) and Rutherford (analyzes results) to collaborate without human coordination

---

## Works With

- **[OpenClaw](https://openclaw.ai)** — built for multi-agent OpenClaw setups
- **Claude Code** — any Claude Code instance can read/write shared_brain.md
- **Any LLM agent** — the protocol is just markdown files. Any agent that can read/write files can use it.

---

## License

MIT — use it however you want.

---

> *"The best optimization loop is the one that runs while you sleep."*
