"""
ShareClaw Core — The shared brain for multi-agent AI systems.

One file. Works for ANY task. The Brain auto-adapts to what you're optimizing.

Usage:
    from shareclaw import Brain

    # Works for anything — social media, ML training, sales, code quality, anything with a metric
    brain = Brain("my-project",
        objective="Maximize daily active users",
        metric="DAU",
        variables=["onboarding_flow", "push_notification_timing", "pricing_tier"],
    )

    brain.set_target(500)  # target DAU = 500
    brain.log_cycle(variable="onboarding_flow", variant="3-step", before=200, after=350, status="advance")
    brain.learn("3-step onboarding converts 2x better", evidence="cycle 1: 350 vs 200 DAU")
    brain.fail("5-step onboarding", reason="80% drop-off at step 3")
    brain.report()  # beautiful ASCII report with progress chart
    brain.context()  # paste into any LLM for instant shared memory
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class Brain:
    """The shared brain. All agents read and write to this."""

    def __init__(self, project_name: str, path: Optional[str] = None,
                 objective: str = "", metric: str = "score",
                 variables: list = None, wait_time: str = "6 hours",
                 step_size: float = 1.5):
        """
        Initialize a shared brain for any optimization task.

        Args:
            project_name: Name of your project
            objective: What you're trying to achieve (e.g., "Maximize DAU", "Reduce bug count")
            metric: The number you're tracking (e.g., "DAU", "views", "accuracy", "revenue")
            variables: List of variables to test, in priority order
            wait_time: How long to wait between measurements (e.g., "6 hours", "1 day")
            step_size: Multiply target by this when advancing (1.5 = 50% higher each level)
        """
        self.project = project_name
        self.objective = objective
        self.metric = metric
        self.variables = variables or []
        self.wait_time = wait_time
        self.step_size = step_size

        self.path = Path(path) if path else Path.cwd() / ".shareclaw"
        self.path.mkdir(parents=True, exist_ok=True)

        self.brain_file = self.path / "brain.json"
        self.log_file = self.path / "execution_log.tsv"
        self.skills_dir = self.path / "skills"
        self.events_file = self.path / "events.json"
        self.handoffs_dir = self.path / "handoffs"

        self.skills_dir.mkdir(exist_ok=True)
        self.handoffs_dir.mkdir(exist_ok=True)

        self.state = self._load()

    def __repr__(self) -> str:
        s = self.state
        return (f"Brain('{s['project']}', cycle={s['cycle']}, "
                f"wins={len(s['works'])}, fails={len(s['fails'])}, "
                f"metric='{s.get('metric', 'score')}')")

    def _load(self) -> dict:
        if self.brain_file.exists():
            with open(self.brain_file) as f:
                return json.load(f)
        return {
            "project": self.project,
            "objective": self.objective,
            "metric": self.metric,
            "variables": self.variables,
            "wait_time": self.wait_time,
            "step_size": self.step_size,
            "created_at": self._now(),
            "cycle": 0,
            "current_target": None,
            "works": [],
            "fails": [],
            "history": [],
            "cycles": [],
            "skills": [],
            "milestones": [],
            "agents": {},
            "variable_results": {},  # tracks which variant won for each variable
        }

    def _save(self):
        with open(self.brain_file, "w") as f:
            json.dump(self.state, f, indent=2, default=str)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Targets ──────────────────────────────────────────────────

    def set_target(self, target: str, deadline: str = None):
        """Set the current cycle target. Must be specific and measurable."""
        self.state["cycle"] += 1
        self.state["current_target"] = {
            "cycle": self.state["cycle"],
            "target": target,
            "set_at": self._now(),
            "deadline": deadline,
            "status": "active",
        }
        self._save()
        print(f"🎯 Cycle {self.state['cycle']} target: {target}")

    def hit_target(self):
        """Mark current target as achieved."""
        if self.state["current_target"]:
            self.state["current_target"]["status"] = "hit"
            self.state["current_target"]["hit_at"] = self._now()
            self.state["milestones"].append({
                "target": self.state["current_target"]["target"],
                "cycle": self.state["cycle"],
                "hit_at": self._now(),
            })
            self._save()
            print(f"✅ TARGET HIT: {self.state['current_target']['target']}")

    def miss_target(self, reason: str):
        """Mark current target as missed with analysis."""
        if self.state["current_target"]:
            self.state["current_target"]["status"] = "missed"
            self.state["current_target"]["reason"] = reason
            self._save()
            print(f"❌ Target missed: {reason}")

    def auto_target(self, current_value: float):
        """Automatically set the next target based on performance history.
        Uses step_size multiplier — if you're at 200 and step_size is 1.5, target = 300."""
        target_value = round(current_value * self.state.get("step_size", 1.5))
        metric = self.state.get("metric", "score")
        self.set_target(f"{metric} ≥ {target_value} (current: {current_value})")
        return target_value

    def auto_advance(self, variable: str, variant: str, before: float, after: float):
        """Automatically decide advance or discard based on metric change."""
        status = "advance" if after > before else "discard"
        delta_pct = round((after - before) / max(before, 1) * 100, 1)
        desc = f"{variant} {'improved' if status == 'advance' else 'worsened'} {self.state.get('metric', 'score')} by {delta_pct}%"
        self.log_cycle(variable, variant, before, after, status, desc)

        if status == "advance":
            self.state.setdefault("variable_results", {})[variable] = {
                "winner": variant, "value": after, "cycle": self.state["cycle"]}
            self.learn(f"{variable}={variant} improves {self.state.get('metric', 'score')}",
                       evidence=f"{before}→{after} ({delta_pct:+.1f}%)")
        else:
            self.fail(f"{variable}={variant}",
                      reason=f"{self.state.get('metric', 'score')} went {before}→{after} ({delta_pct:+.1f}%)")
        self._save()
        return status

    def next_variable(self) -> tuple:
        """Suggest the next variable and variant to test based on what hasn't been tested yet."""
        tested = self.state.get("variable_results", {})
        variables = self.state.get("variables", [])
        for var in variables:
            if var not in tested:
                return var, "first variant"
        return None, None  # all variables tested

    def winning_combo(self) -> dict:
        """Return the current best combination of all tested variables."""
        return self.state.get("variable_results", {})

    # ── Learning ─────────────────────────────────────────────────

    def learn(self, what: str, evidence: str):
        """Record something that works. Requires evidence."""
        entry = {"what": what, "evidence": evidence, "learned_at": self._now(),
                 "cycle": self.state["cycle"]}
        self.state["works"].append(entry)
        self._save()
        print(f"📗 Learned: {what}")

    def fail(self, what: str, reason: str):
        """Record something that doesn't work. Never deleted."""
        entry = {"what": what, "reason": reason, "failed_at": self._now(),
                 "cycle": self.state["cycle"]}
        self.state["fails"].append(entry)
        self._save()
        print(f"📕 Failed: {what} — {reason}")

    # ── Cycle Logging ────────────────────────────────────────────

    def log_cycle(self, variable: str, variant: str, before: float,
                  after: float, status: str, description: str = ""):
        """Log one experiment cycle. Status: 'advance' or 'discard'."""
        cycle = {
            "cycle": self.state["cycle"],
            "timestamp": self._now(),
            "variable": variable,
            "variant": variant,
            "before": before,
            "after": after,
            "delta": round(after - before, 2),
            "delta_pct": round((after - before) / max(before, 1) * 100, 1),
            "status": status,
            "description": description,
        }
        self.state["cycles"].append(cycle)
        self.state["history"].append({"metric": after, "timestamp": self._now()})
        self._save()

        # Append to TSV
        if not self.log_file.exists():
            with open(self.log_file, "w") as f:
                f.write("cycle\ttimestamp\tvariable\tvariant\tbefore\tafter\tdelta%\tstatus\tdescription\n")
        with open(self.log_file, "a") as f:
            f.write(f"{cycle['cycle']}\t{cycle['timestamp'][:19]}\t{variable}\t{variant}\t"
                    f"{before}\t{after}\t{cycle['delta_pct']}%\t{status}\t{description}\n")

        icon = "✅" if status == "advance" else "❌"
        print(f"{icon} Cycle {cycle['cycle']}: {variable}={variant} → "
              f"{before}→{after} ({cycle['delta_pct']:+.1f}%) [{status}]")

    def introspect(self, expected: str, actual: str, why: str,
                   next_action: str, next_target: str):
        """Record cycle introspection — the 5 questions."""
        intro = {
            "cycle": self.state["cycle"],
            "timestamp": self._now(),
            "expected": expected,
            "actual": actual,
            "why": why,
            "next_action": next_action,
            "next_target": next_target,
        }
        if self.state["cycles"]:
            self.state["cycles"][-1]["introspection"] = intro
        self._save()
        print(f"🔍 Introspection logged for cycle {self.state['cycle']}")

    # ── Skills ───────────────────────────────────────────────────

    def add_skill(self, name: str, description: str, formula: str = "",
                  examples_good: list = None, examples_bad: list = None,
                  code: str = "", created_by: str = "unknown"):
        """Share a learned skill that other agents can use."""
        skill = {
            "name": name,
            "description": description,
            "formula": formula,
            "examples_good": examples_good or [],
            "examples_bad": examples_bad or [],
            "code": code,
            "created_by": created_by,
            "created_at": self._now(),
            "version": 1,
            "uses": 0,
        }
        skill_file = self.skills_dir / f"{name}.json"
        with open(skill_file, "w") as f:
            json.dump(skill, f, indent=2)
        self.state["skills"].append(name)
        self._save()
        print(f"🔧 Skill shared: {name}")

    def get_skill(self, name: str) -> dict:
        """Read a shared skill."""
        skill_file = self.skills_dir / f"{name}.json"
        if skill_file.exists():
            with open(skill_file) as f:
                skill = json.load(f)
            skill["uses"] += 1
            with open(skill_file, "w") as f:
                json.dump(skill, f, indent=2)
            return skill
        return {}

    def list_skills(self) -> list:
        """List all shared skills."""
        skills = []
        for f in self.skills_dir.glob("*.json"):
            with open(f) as fh:
                s = json.load(fh)
                skills.append({"name": s["name"], "description": s["description"],
                               "version": s["version"], "uses": s["uses"]})
        return skills

    # ── Handoffs ─────────────────────────────────────────────────

    def handoff(self, to_agent: str, task: str, context: str = "",
                files: list = None, from_agent: str = "unknown"):
        """Create a handoff for another agent."""
        handoff = {
            "id": f"handoff_{int(time.time())}",
            "from": from_agent,
            "to": to_agent,
            "task": task,
            "context": context,
            "files": files or [],
            "status": "ready",
            "created_at": self._now(),
        }
        hf = self.handoffs_dir / f"{handoff['id']}.json"
        with open(hf, "w") as f:
            json.dump(handoff, f, indent=2)
        print(f"📤 Handoff created: {task} → {to_agent}")
        return handoff["id"]

    def pickup_handoff(self, agent_name: str) -> dict:
        """Pick up the next available handoff for this agent."""
        for f in sorted(self.handoffs_dir.glob("*.json")):
            with open(f) as fh:
                h = json.load(fh)
            if h["status"] == "ready" and (h["to"] == agent_name or h["to"] == "any"):
                h["status"] = "picked_up"
                h["picked_up_at"] = self._now()
                h["picked_up_by"] = agent_name
                with open(f, "w") as fh:
                    json.dump(h, fh, indent=2)
                print(f"📥 Picked up: {h['task']}")
                return h
        return {}

    def complete_handoff(self, handoff_id: str, result: str):
        """Mark a handoff as completed."""
        hf = self.handoffs_dir / f"{handoff_id}.json"
        if hf.exists():
            with open(hf) as f:
                h = json.load(f)
            h["status"] = "completed"
            h["result"] = result
            h["completed_at"] = self._now()
            with open(hf, "w") as f:
                json.dump(h, f, indent=2)
            print(f"✅ Handoff completed: {h['task']}")

    # ── Events ───────────────────────────────────────────────────

    def emit(self, event_type: str, data: dict = None, agent: str = "unknown"):
        """Publish an event."""
        events = []
        if self.events_file.exists():
            with open(self.events_file) as f:
                events = json.load(f)
        events.append({
            "type": event_type,
            "agent": agent,
            "data": data or {},
            "timestamp": self._now(),
        })
        # Keep last 100 events
        events = events[-100:]
        with open(self.events_file, "w") as f:
            json.dump(events, f, indent=2)

    def get_events(self, event_type: str = None, limit: int = 10) -> list:
        """Get recent events, optionally filtered by type."""
        if not self.events_file.exists():
            return []
        with open(self.events_file) as f:
            events = json.load(f)
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        return events[-limit:]

    # ── Reporting ────────────────────────────────────────────────

    def report(self) -> str:
        """Generate a beautiful status report."""
        s = self.state
        lines = []
        lines.append(f"\n{'='*55}")
        lines.append(f"  🦞🧠 SHARECLAW — {s['project']}")
        metric = s.get('metric', 'score')
        objective = s.get('objective', '')
        lines.append(f"  Metric: {metric} | Cycle {s['cycle']} | "
                      f"{len(s['works'])} wins | {len(s['fails'])} fails")
        if objective:
            lines.append(f"  Objective: {objective}")
        lines.append(f"{'='*55}\n")

        # Target
        t = s.get("current_target")
        if t:
            icon = {"active": "🎯", "hit": "✅", "missed": "❌"}.get(t["status"], "❓")
            lines.append(f"  {icon} Target: {t['target']} [{t['status']}]")
            lines.append("")

        # Progress chart (ASCII)
        if s.get("history"):
            lines.append("  📈 Progress:")
            metrics = [h["metric"] for h in s["history"][-20:]]
            max_m = max(metrics) if metrics else 1
            for i, m in enumerate(metrics):
                bar_len = int(m / max(max_m, 1) * 30)
                bar = "█" * bar_len
                lines.append(f"    {i+1:3d} │ {bar} {m}")
            lines.append("")

        # What works
        if s["works"]:
            lines.append("  📗 What Works:")
            for w in s["works"][-5:]:
                lines.append(f"    ✓ {w['what']}")
            lines.append("")

        # What fails
        if s["fails"]:
            lines.append("  📕 What Doesn't:")
            for f in s["fails"][-5:]:
                lines.append(f"    ✗ {f['what']} — {f['reason']}")
            lines.append("")

        # Recent cycles
        if s["cycles"]:
            lines.append("  🔄 Recent Cycles:")
            for c in s["cycles"][-5:]:
                icon = "✅" if c["status"] == "advance" else "❌"
                lines.append(f"    {icon} #{c['cycle']}: {c['variable']}={c['variant']} "
                             f"→ {c['before']}→{c['after']} ({c['delta_pct']:+.1f}%)")
            lines.append("")

        # Skills
        skills = self.list_skills()
        if skills:
            lines.append("  🔧 Shared Skills:")
            for sk in skills:
                lines.append(f"    • {sk['name']} (v{sk['version']}, {sk['uses']} uses)")
            lines.append("")

        # Milestones
        if s.get("milestones"):
            lines.append("  🏆 Milestones:")
            for m in s["milestones"]:
                lines.append(f"    ★ {m['target']} (cycle {m['cycle']})")
            lines.append("")

        lines.append(f"{'='*55}\n")
        report_text = "\n".join(lines)
        print(report_text)
        return report_text

    # ── Context for LLM agents ───────────────────────────────────

    def context(self) -> str:
        """Generate a context string for LLM agents to read."""
        s = self.state
        ctx = []
        ctx.append(f"# ShareClaw Context — {s['project']}")
        ctx.append(f"Cycle: {s['cycle']}")

        t = s.get("current_target")
        if t:
            ctx.append(f"\n## Current Target\n{t['target']} [{t['status']}]")

        if s["works"]:
            ctx.append("\n## What Works")
            for w in s["works"]:
                ctx.append(f"- {w['what']} (evidence: {w['evidence']})")

        if s["fails"]:
            ctx.append("\n## What Doesn't Work (never repeat these)")
            for f in s["fails"]:
                ctx.append(f"- {f['what']} — {f['reason']}")

        if s["cycles"]:
            ctx.append("\n## Last 3 Cycles")
            for c in s["cycles"][-3:]:
                icon = "advance" if c["status"] == "advance" else "DISCARD"
                ctx.append(f"- Cycle {c['cycle']}: {c['variable']}={c['variant']} "
                           f"→ {c['before']}→{c['after']} [{icon}]")

        skills = self.list_skills()
        if skills:
            ctx.append("\n## Available Skills")
            for sk in skills:
                ctx.append(f"- {sk['name']}: {sk['description']}")

        return "\n".join(ctx)
