# Shared Skills Protocol

When one agent learns a new capability, ALL agents should benefit. This protocol defines how agents share skills.

## How It Works

```
Agent A discovers a working approach → writes it to skills/
                                              ↓
Agent B reads skills/ before acting → uses Agent A's approach
                                              ↓
Agent B improves the skill → updates skills/ with improvements
```

## Skill File Format

Each shared skill is a markdown file in `skills/`:

```markdown
---
name: ragebait-hooks
created_by: heisenberg
created_at: 2026-03-21
version: 3
success_rate: 72%
---

# Ragebait Hooks

## What This Skill Does
Generates high-engagement TikTok hooks using ragebait patterns.

## When To Use
When creating content that needs to stop the scroll and trigger comments.

## The Formula
1. Start with a SHOCKING personal claim (line 1-2)
2. Mention something relatable that triggers jealousy (line 3-4)
3. Drop the product/solution naturally (line 5-6)
4. End with something that makes people want to comment

## Examples That Worked (with data)
- "everyone calls me the TAYLOR SWIFT of MATH" → 450 views, 2.9% eng
- "DUMBEST PERSON in my class found this app" → 380 views, 3.1% eng

## Examples That Failed (with data)
- "step by step out loud for free" → 200 views, 1% eng (too promotional)

## How To Use
```python
hook = generate_ragebait_hook(
    claim="TAYLOR SWIFT of MATH",
    product="Professor Curious app",
    contrast="ChatGPT",
    ending="now they think i'm a genius"
)
```

## Version History
- v1: Basic ragebait (200 views avg)
- v2: Added CAPS on keywords (300 views avg)
- v3: Removed product from first 2 lines (450 views avg)
```

## Rules

1. **Any agent can create a skill** — just write a file to `skills/`
2. **Any agent can improve a skill** — increment the version, explain what changed
3. **Include data** — every skill must have success/failure examples with real numbers
4. **Include when NOT to use** — failed contexts are as valuable as successful ones
5. **Skills are living documents** — they improve with every cycle
