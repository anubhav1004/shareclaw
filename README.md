<p align="center">
  <img src="assets/banner.png" alt="ShareClaw" width="100%">
</p>

# 🧠 ShareClaw

> *It's March 2026. You have two AI agents — Heisenberg generates TikTok content, Rutherford analyzes what performs. They've been running for a week. Heisenberg just posted a video that got 5x more views than anything before. How? Because Rutherford wrote in the shared brain that ragebait hooks outperform motivational ones by 2x — and Heisenberg read that before creating the next batch. Neither agent was told this by a human. They figured it out together.*

**ShareClaw** gives multiple AI agents a shared brain. They read before acting, write after acting, set their own targets, and get smarter every cycle. It's [autoresearch](https://github.com/karpathy/autoresearch) but for any task, not just ML training — and it works across multiple agents, not just one.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Agent A    │────▶│   shared_brain   │◀────│   Agent B    │
│  (creates)   │     │       .md        │     │  (analyzes)  │
│              │     │                  │     │              │
│  reads what  │     │  • what works    │     │  writes what │
│  B learned   │     │  • what doesn't  │     │  it found    │
│  before each │     │  • current target│     │  after each  │
│  action      │     │  • cycle log     │     │  measurement │
└─────────────┘     └──────────────────┘     └─────────────┘
                            │
                    ┌───────▼───────┐
                    │ execution_log │
                    │    .tsv       │
                    │               │
                    │ cycle 1: ✅   │
                    │ cycle 2: ❌   │
                    │ cycle 3: ✅   │
                    └───────────────┘
```

Seeing as there seems to be a lot of interest in making AI agents actually learn from their own experience (rather than just following instructions), I'm sharing the system we built and tested in production. It's three markdown files and a protocol. That's it.

---

## How it works

ShareClaw is three files and a set of rules:

### 1. `shared_brain.md` — the living state

This is the shared memory. Every agent reads it before acting and writes to it after acting. It contains:

```markdown
## Current Target
Cycle: 4
Target: Get avg views above 1,000 (currently 450)
Variable being tested: video format — vlog montage vs single scene
Deadline: Check results by tomorrow morning

## What We Know Works
1. Ragebait hooks ("everyone calls me the TAYLOR SWIFT of MATH")
   get 2x more views than motivational hooks — confirmed cycle 1 vs 2
2. 4 hashtags from competitor data > 12 random hashtags — confirmed cycle 3
3. Chopin Nocturne No. 2 audio doesn't get muted — confirmed

## What We Know Doesn't Work
1. Long 8-line text overlays — 200 views avg, killed in cycle 1
2. Mentioning product in first 2 lines — looks like an ad, killed in cycle 2
3. Copyrighted trending audio — gets muted by TikTok, killed in cycle 3

## Cycle Log

### Cycle 3 (just completed)
Target: 500 views on at least one video
Variable: hook style → ragebait vs challenge
Result: ADVANCE ✅ — ragebait got 450 avg, challenge got 200

Introspection:
1. What did we expect? Ragebait to outperform based on competitor data
2. What actually happened? 450 vs 200. Ragebait won decisively.
3. Why? Ragebait triggers emotional response — jealousy, curiosity, controversy
4. What next? Keep ragebait, now test video FORMAT
5. Next target? 1,000 views (2x current best)
```

The key insight: **what works and what doesn't are append-only**. Agents never delete failed experiments — they learn from them. Over 10 cycles, this becomes a goldmine of institutional knowledge.

### 2. `execution.md` — the autonomous loop

Inspired by [Karpathy's autoresearch program.md](https://github.com/karpathy/autoresearch/blob/master/program.md). It tells the agent: loop forever, test one variable at a time, keep what works, discard what doesn't.

```markdown
## The Loop

LOOP FOREVER:
  1. Read shared_brain.md
  2. MEASURE current metrics
  3. Did last cycle hit its target?
     - YES → set HIGHER target, keep the winning variable
     - NO  → revert, try a different variable
  4. Change ONE variable (never more than one)
  5. Execute
  6. Wait for results (6 hours, 24 hours, whatever your domain needs)
  7. Measure again
  8. Log result: advance ✅ or discard ❌
  9. Write introspection to shared_brain.md
  10. GOTO 1

Do NOT pause to ask the human if you should continue.
The loop runs until the human interrupts you, period.
```

### 3. `execution_log.tsv` — the append-only record

Every cycle gets one line. Over time this becomes your experiment history:

```
cycle  timestamp            variable     variant    before  after  status   description
1      2026-03-21T12:00:00  hook_style   motivational  200    200  discard  no improvement over baseline
2      2026-03-21T18:00:00  hook_style   ragebait      200    450  advance  ragebait 2.25x better
3      2026-03-22T06:00:00  hook_style   challenge     200    180  discard  worse than baseline
4      2026-03-22T12:00:00  format       vlog          450    600  advance  vlog + ragebait = best combo
5      2026-03-22T18:00:00  format       aesthetic     450    350  discard  aesthetic underperformed
6      2026-03-23T06:00:00  audio        chopin        600    750  advance  chopin + vlog + ragebait
```

After 6 cycles you know: **ragebait hooks + vlog format + chopin audio = 750 views** (up from 200 baseline). No human told the agents this. They figured it out by testing one variable at a time.

---

## The Introspection Protocol

This is what makes ShareClaw different from just "saving state to a file." After every cycle, agents must answer five questions **in the shared brain**:

```
1. What did we expect? → forces agents to have a hypothesis
2. What actually happened? → forces agents to look at real data
3. Why do we think it happened? → forces analysis, not just observation
4. What should we try next? → forces forward-thinking
5. What is the specific target for next cycle? → forces commitment to a number
```

Without this, agents just log "posted 3 videos" and move on. With this, they log "posted 3 ragebait videos, expected 500 views, got 450, probably because the account is still warming up, next cycle will test a different video format while keeping ragebait hooks, target: 600 views."

---

## Quick start

```bash
# Clone
git clone https://github.com/anubhav1004/shareclaw.git
cd shareclaw

# Copy templates to your project
cp templates/shared_brain.md /path/to/your/project/shared_brain.md
cp templates/execution.md /path/to/your/project/execution.md
cp templates/execution_log.tsv /path/to/your/project/execution_log.tsv

# Edit shared_brain.md — set your initial target and context
# Edit execution.md — define your variables to test and constraints
```

Then tell your agents about it. In your agent's system prompt or config:

```
CRITICAL: Read /path/to/shared_brain.md BEFORE every task.
Write results AFTER every task. Follow the introspection protocol.
Set specific numeric targets. Keep what works, discard what doesn't.
```

That's it. Your agents now share a brain.

---

## For OpenClaw users

If you're running [OpenClaw](https://openclaw.ai) with multiple agents, add this to each agent's identity theme in `openclaw.json`:

```json
{
  "agents": {
    "list": [
      {
        "id": "agent-a",
        "identity": {
          "theme": "... CRITICAL OVERRIDE FOR SHARED BRAIN: Read /home/node/.openclaw/workspace/shared_brain.md BEFORE every task. Write results AFTER every task. Follow the introspection protocol. Set specific numeric targets. ..."
        }
      },
      {
        "id": "agent-b",
        "identity": {
          "theme": "... [same override] ..."
        }
      }
    ]
  }
}
```

Both agents now read and write to the same file. Agent A's learnings are immediately available to Agent B.

---

## For Claude Code users

If you're using Claude Code (Anthropic's CLI), ShareClaw works through the project memory system:

```bash
# Add shared brain to your Claude Code project
cp templates/shared_brain.md .claude/projects/your-project/memory/shared_brain.md
```

Or just keep `shared_brain.md` in your repo root — Claude Code reads files in the working directory.

---

## For any LLM agent

ShareClaw is just markdown files. Any agent that can read and write files can use it:

```python
# Python example — agent reads shared brain before acting
def run_cycle():
    # 1. Read shared brain
    with open("shared_brain.md") as f:
        brain = f.read()

    # 2. Parse current target
    target = extract_target(brain)  # "500 views"

    # 3. Execute (your domain-specific action)
    result = execute_action(target)

    # 4. Measure
    metric = measure_result()

    # 5. Evaluate
    if metric >= target:
        status = "advance"
        new_target = target * 1.5  # raise the bar
    else:
        status = "discard"
        new_target = target  # try different variable

    # 6. Write back to shared brain
    update_shared_brain("shared_brain.md", {
        "cycle_result": status,
        "metric": metric,
        "introspection": {
            "expected": target,
            "actual": metric,
            "why": analyze_why(metric, target),
            "next": decide_next_variable(),
            "next_target": new_target,
        }
    })

    # 7. Log
    append_to_log("execution_log.tsv", cycle_data)
```

```javascript
// Node.js example — agent reads shared brain
const fs = require('fs');

async function runCycle() {
  // Read shared brain
  const brain = fs.readFileSync('shared_brain.md', 'utf-8');
  const target = parseTarget(brain);

  // Execute
  const result = await executeAction(target);
  const metric = await measure();

  // Evaluate + write back
  const status = metric >= target ? 'advance' : 'discard';
  updateSharedBrain('shared_brain.md', { status, metric, target });
  appendLog('execution_log.tsv', { cycle: getCycleNum(), status, metric });
}
```

---

## Project structure

```
shareclaw/
├── README.md                          # you are here
├── templates/
│   ├── shared_brain.md                # copy this → your project
│   ├── execution.md                   # copy this → your project
│   └── execution_log.tsv             # copy this → your project
└── examples/
    ├── tiktok-growth/                 # real-world: social media optimization
    │   ├── README.md
    │   ├── shared_brain.md            # actual state from production use
    │   └── execution.md              # actual loop program
    └── content-pipeline/             # multi-agent content creation
        ├── README.md
        └── shared_brain.md
```

---

## Design decisions

**Why markdown and not a database?**
Because every LLM can read and write markdown. No setup, no dependencies, no API. Just a file. Also, markdown is human-readable — you can open `shared_brain.md` and immediately understand the system's current state.

**Why one variable at a time?**
Because if you change the hook AND the format AND the audio in the same cycle, and views go up, you don't know which change caused it. One variable per cycle = clean signal.

**Why append-only for "what doesn't work"?**
Because the most expensive mistake is repeating a failed experiment. If Agent A tested "long motivational hooks" and they flopped, Agent B should never try them again. But if you delete the failure, Agent B doesn't know.

**Why specific numeric targets?**
Because "improve engagement" is meaningless. "Get to 500 views per post" is testable. If you hit it, you know. If you don't, you know. Vague targets lead to vague actions.

**Why introspection questions?**
Because without them, agents just log what they did, not what they learned. The five questions force reflection: hypothesis → data → analysis → decision → commitment. This is what separates a learning system from a logging system.

---

## What people are building with ShareClaw

*(If you build something cool, open a PR to add it here)*

- **TikTok growth engine** — autonomous content optimization across hooks, formats, audio, posting times
- **Instagram reel optimization** — multi-format testing for education app marketing
- **Content quality iteration** — Agent A writes, Agent B reviews, quality score improves each cycle

---

## License

MIT — use it for anything.

---

> *"Two agents sharing a brain is worth ten agents working alone."*

---

## 📋 Full Protocol Suite

ShareClaw isn't just shared memory. It's a complete multi-agent collaboration framework:

| Protocol | File | What It Does |
|----------|------|-------------|
| **Shared Brain** | `shared_brain.md` | Living state — targets, learnings, cycle log |
| **Shared Skills** | [`protocols/shared_skills.md`](protocols/shared_skills.md) | Agents teach each other capabilities |
| **Agent Handoff** | [`protocols/handoff.md`](protocols/handoff.md) | Clean work passing between agents |
| **Task Queue** | [`protocols/task_queue.md`](protocols/task_queue.md) | Shared todo list any agent can pick up |
| **Consensus** | [`protocols/consensus.md`](protocols/consensus.md) | Multi-agent voting on decisions |
| **Event System** | [`protocols/events.md`](protocols/events.md) | Agents publish/subscribe to events |
| **Execution Loop** | `execution.md` | Autonomous self-improving loop |

### Shared Skills — agents teaching agents

When Agent A figures out that ragebait hooks get 2x more views, it writes a skill file. Agent B reads it and immediately knows the formula, the examples that worked, and the examples that failed:

```
skills/
├── ragebait-hooks.md      # v3, 72% success rate
├── video-text-overlay.md   # v2, 95% success rate
└── trend-scraping.md       # v1, 88% success rate
```

Each skill has: what it does, when to use it, when NOT to use it, code examples, version history, and real performance data. Skills improve with every cycle. See [`protocols/shared_skills.md`](protocols/shared_skills.md).

### Agent Handoff — no dropped balls

Agent A generates videos. Agent B needs to post them. The handoff protocol ensures nothing falls through the cracks:

```
Agent A: "I'm done. Here are the files. Here's what needs to happen next."
Agent B: "Picked up. Working on it."
Agent B: "Done. Results in shared_brain.md."
```

See [`protocols/handoff.md`](protocols/handoff.md).

### Task Queue — shared todo list

Any agent can add tasks. Any agent can pick them up. High priority tasks get picked up within 30 minutes:

```markdown
- [ ] **[HIGH]** Check analytics — assigned: any — deadline: tonight
- [~] **[MED]** Generate videos — assigned: heisenberg — started: 2pm
- [x] **[LOW]** Refresh audio — completed by: rutherford — result: 3 new tracks
```

See [`protocols/task_queue.md`](protocols/task_queue.md).

### Consensus — resolving disagreements

When agents disagree, they vote with data:

```
Agent A: NO — ragebait is working, don't change (data: 450 views)
Agent B: YES — challenge hooks get more comments (data: competitor analysis)
Resolution: TIE → keep current + test 1 challenge alongside ragebait
```

See [`protocols/consensus.md`](protocols/consensus.md).

### Event System — real-time coordination

Agents publish events. Other agents react:

```
VIDEO_POSTED → analytics agent starts 6h countdown
ANALYTICS_READY → strategy agent updates shared brain
TARGET_HIT → all agents celebrate + set higher target
ALERT → humans get notified
```

See [`protocols/events.md`](protocols/events.md).
