"""
ShareClaw Core — Shared memory + self-improving coordination for multi-agent systems.

The Brain keeps durable shared state, emits events, coordinates handoffs, and now
ships first-class task queue + consensus primitives on top of safe file locking.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    import fcntl  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None


PRIORITY_ORDER = {"HIGH": 0, "MED": 1, "LOW": 2}
TASK_STATUS_ORDER = {"pending": 0, "in_progress": 1, "blocked": 2, "completed": 3}


class Brain:
    """The shared brain that agents read before acting and update after acting."""

    def __init__(
        self,
        project_name: str,
        path: Optional[str] = None,
        objective: str = "",
        metric: str = "score",
        variables: Optional[List[str]] = None,
        wait_time: str = "6 hours",
        step_size: float = 1.5,
    ):
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
        self.tasks_file = self.path / "tasks.json"
        self.decisions_file = self.path / "decisions.json"
        self.lock_file = self.path / ".lock"

        self.shared_brain_markdown_file = self.path / "shared_brain.md"
        self.task_queue_markdown_file = self.path / "task_queue.md"
        self.events_markdown_file = self.path / "events.md"
        self.decisions_markdown_file = self.path / "decisions.md"

        self.skills_dir.mkdir(exist_ok=True)
        self.handoffs_dir.mkdir(exist_ok=True)

        with self._locked():
            self.state = self._load_state_unlocked()
            self._sync_markdown_mirrors_unlocked()

    def __repr__(self) -> str:
        s = self.state
        return (
            f"Brain('{s['project']}', cycle={s['cycle']}, "
            f"wins={len(s['works'])}, fails={len(s['fails'])}, "
            f"metric='{s.get('metric', 'score')}')"
        )

    def files(self) -> Dict[str, str]:
        """Return the key files agents and humans should care about."""
        return {
            "state_json": str(self.brain_file),
            "shared_brain_md": str(self.shared_brain_markdown_file),
            "execution_log_tsv": str(self.log_file),
            "task_queue_md": str(self.task_queue_markdown_file),
            "events_md": str(self.events_markdown_file),
            "decisions_md": str(self.decisions_markdown_file),
            "skills_dir": str(self.skills_dir),
            "handoffs_dir": str(self.handoffs_dir),
        }

    def _default_state(self) -> Dict[str, Any]:
        return {
            "project": self.project,
            "objective": self.objective,
            "metric": self.metric,
            "variables": self.variables,
            "wait_time": self.wait_time,
            "step_size": self.step_size,
            "created_at": self._now(),
            "last_updated_at": self._now(),
            "cycle": 0,
            "current_target": None,
            "works": [],
            "fails": [],
            "history": [],
            "cycles": [],
            "skills": [],
            "milestones": [],
            "agents": {},
            "variable_results": {},
        }

    @contextmanager
    def _locked(self):
        self.lock_file.touch(exist_ok=True)
        with open(self.lock_file, "a+", encoding="utf-8") as handle:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _load_state_unlocked(self) -> Dict[str, Any]:
        if self.brain_file.exists():
            with open(self.brain_file, encoding="utf-8") as f:
                return json.load(f)
        return self._default_state()

    def _save_state_unlocked(self):
        self.state["last_updated_at"] = self._now()
        with open(self.brain_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, default=str)

    def _read_json_unlocked(self, path: Path, default: Any) -> Any:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return deepcopy(default)

    def _write_json_unlocked(self, path: Path, data: Any):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _read_tasks_unlocked(self) -> List[Dict[str, Any]]:
        return self._read_json_unlocked(self.tasks_file, [])

    def _write_tasks_unlocked(self, tasks: List[Dict[str, Any]]):
        self._write_json_unlocked(self.tasks_file, tasks)

    def _read_decisions_unlocked(self) -> List[Dict[str, Any]]:
        return self._read_json_unlocked(self.decisions_file, [])

    def _write_decisions_unlocked(self, decisions: List[Dict[str, Any]]):
        self._write_json_unlocked(self.decisions_file, decisions)

    def _read_events_unlocked(self) -> List[Dict[str, Any]]:
        return self._read_json_unlocked(self.events_file, [])

    def _write_events_unlocked(self, events: List[Dict[str, Any]]):
        self._write_json_unlocked(self.events_file, events)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:10]}"

    def _normalize_priority(self, priority: str) -> str:
        normalized = (priority or "MED").upper()
        aliases = {"MEDIUM": "MED"}
        normalized = aliases.get(normalized, normalized)
        if normalized not in PRIORITY_ORDER:
            raise ValueError("priority must be one of HIGH, MED, LOW")
        return normalized

    def _normalize_choice(self, options: List[str], choice: str) -> str:
        for option in options:
            if option.lower() == choice.lower():
                return option
        return choice

    def _task_sort_key(self, task: Dict[str, Any]):
        return (
            TASK_STATUS_ORDER.get(task["status"], 99),
            PRIORITY_ORDER.get(task.get("priority", "MED"), 99),
            task.get("created_at", ""),
            task["id"],
        )

    def _decision_counts(self, decision: Dict[str, Any]) -> Counter:
        return Counter(v["choice"] for v in decision.get("votes", []))

    def _decision_summary(self, decision: Dict[str, Any]) -> str:
        counts = self._decision_counts(decision)
        if not counts:
            return "no votes yet"
        return ", ".join(
            f"{choice}: {count}"
            for choice, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        )

    def _list_skills_unlocked(self) -> List[Dict[str, Any]]:
        skills = []
        for path in sorted(self.skills_dir.glob("*.json")):
            with open(path, encoding="utf-8") as fh:
                skill = json.load(fh)
            skills.append(
                {
                    "name": skill["name"],
                    "description": skill["description"],
                    "version": skill["version"],
                    "uses": skill["uses"],
                    "updated_at": skill.get("updated_at", skill.get("created_at")),
                }
            )
        return skills

    def _append_log_row_unlocked(self, cycle: Dict[str, Any]):
        if not self.log_file.exists():
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(
                    "cycle\ttimestamp\tvariable\tvariant\tbefore\tafter\tdelta%\tstatus\tdescription\n"
                )

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(
                f"{cycle['cycle']}\t{cycle['timestamp'][:19]}\t{cycle['variable']}\t"
                f"{cycle['variant']}\t{cycle['before']}\t{cycle['after']}\t"
                f"{cycle['delta_pct']}%\t{cycle['status']}\t{cycle['description']}\n"
            )

    def _append_event_unlocked(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        agent: str = "unknown",
        details: str = "",
    ) -> Dict[str, Any]:
        events = self._read_events_unlocked()
        event = {
            "id": self._new_id("event"),
            "type": event_type,
            "agent": agent,
            "details": details,
            "data": data or {},
            "timestamp": self._now(),
        }
        events.append(event)
        self._write_events_unlocked(events[-100:])
        return event

    def _set_target_unlocked(self, target: str, deadline: Optional[str] = None) -> Dict[str, Any]:
        self.state["cycle"] += 1
        current_target = {
            "cycle": self.state["cycle"],
            "target": target,
            "set_at": self._now(),
            "deadline": deadline,
            "status": "active",
        }
        self.state["current_target"] = current_target
        return current_target

    def _learn_unlocked(self, what: str, evidence: str) -> Dict[str, Any]:
        entry = {
            "what": what,
            "evidence": evidence,
            "learned_at": self._now(),
            "cycle": self.state["cycle"],
        }
        self.state["works"].append(entry)
        return entry

    def _fail_unlocked(self, what: str, reason: str) -> Dict[str, Any]:
        entry = {
            "what": what,
            "reason": reason,
            "failed_at": self._now(),
            "cycle": self.state["cycle"],
        }
        self.state["fails"].append(entry)
        return entry

    def _log_cycle_unlocked(
        self,
        variable: str,
        variant: str,
        before: float,
        after: float,
        status: str,
        description: str = "",
    ) -> Dict[str, Any]:
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
        self.state["history"].append({"metric": after, "timestamp": cycle["timestamp"]})
        if status == "advance":
            self.state.setdefault("variable_results", {})[variable] = {
                "winner": variant,
                "value": after,
                "cycle": self.state["cycle"],
            }
        self._append_log_row_unlocked(cycle)
        return cycle

    def _fallback_choice(self, decision: Dict[str, Any]) -> str:
        policy = decision.get("default_policy", "keep_current")
        options = decision.get("options", [])
        if policy == "keep_current":
            return "KEEP_CURRENT"
        if policy == "defer":
            return "DEFER"
        if policy in options:
            return policy
        if options:
            return options[0]
        return "KEEP_CURRENT"

    def _render_shared_brain_markdown(
        self,
        state: Dict[str, Any],
        tasks: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
        skills: List[Dict[str, Any]],
    ) -> str:
        lines = [
            f"# Shared Brain — {state['project']}",
            "",
            "> Auto-generated by ShareClaw. JSON is the source of truth; this markdown mirror is for humans and agents.",
            "",
            f"- Objective: {state.get('objective') or 'Not set yet'}",
            f"- Metric: {state.get('metric', 'score')}",
            f"- Wait time: {state.get('wait_time', 'Not set')}",
            f"- Step size: x{state.get('step_size', 1.5)}",
            f"- Updated: {state.get('last_updated_at', state.get('created_at', self._now()))}",
            "",
            "## Current Target",
        ]

        target = state.get("current_target")
        if target:
            lines.extend(
                [
                    f"- Cycle: {target['cycle']}",
                    f"- Target: {target['target']}",
                    f"- Status: {target['status']}",
                    f"- Deadline: {target.get('deadline') or 'None'}",
                    "",
                ]
            )
        else:
            lines.extend(["No active target yet.", ""])

        lines.append("## What Works")
        if state["works"]:
            for item in state["works"][-10:]:
                lines.append(f"- {item['what']} (evidence: {item['evidence']})")
        else:
            lines.append("- No confirmed wins yet.")
        lines.append("")

        lines.append("## What Doesn't Work")
        if state["fails"]:
            for item in state["fails"][-10:]:
                lines.append(f"- {item['what']} — {item['reason']}")
        else:
            lines.append("- No failures logged yet.")
        lines.append("")

        lines.append("## Winning Combo")
        if state.get("variable_results"):
            for variable, result in state["variable_results"].items():
                lines.append(
                    f"- {variable}: {result['winner']} "
                    f"(value: {result['value']}, cycle: {result['cycle']})"
                )
        else:
            lines.append("- No winning variables recorded yet.")
        lines.append("")

        lines.append("## Recent Cycles")
        if state["cycles"]:
            lines.append("| Cycle | Variable | Variant | Before | After | Delta | Status |")
            lines.append("|-------|----------|---------|--------|-------|-------|--------|")
            for cycle in state["cycles"][-8:]:
                lines.append(
                    f"| {cycle['cycle']} | {cycle['variable']} | {cycle['variant']} | "
                    f"{cycle['before']} | {cycle['after']} | {cycle['delta_pct']}% | {cycle['status']} |"
                )
        else:
            lines.append("No cycles logged yet.")
        lines.append("")

        recent_introspection = [
            cycle for cycle in state["cycles"][-5:] if "introspection" in cycle
        ]
        lines.append("## Introspection")
        if recent_introspection:
            for cycle in recent_introspection:
                intro = cycle["introspection"]
                lines.extend(
                    [
                        f"### Cycle {cycle['cycle']}",
                        f"1. Expected: {intro['expected']}",
                        f"2. Actual: {intro['actual']}",
                        f"3. Why: {intro['why']}",
                        f"4. Next action: {intro['next_action']}",
                        f"5. Next target: {intro['next_target']}",
                        "",
                    ]
                )
        else:
            lines.extend(["No introspection entries yet.", ""])

        active_tasks = [t for t in tasks if t["status"] in {"pending", "in_progress", "blocked"}]
        lines.append("## Active Task Queue")
        if active_tasks:
            for task in sorted(active_tasks, key=self._task_sort_key)[:10]:
                extra = []
                if task.get("deadline"):
                    extra.append(f"deadline: {task['deadline']}")
                if task.get("assigned_to"):
                    extra.append(f"assigned: {task['assigned_to']}")
                lines.append(
                    f"- [{task['status']}] [{task['priority']}] {task['title']}"
                    + (f" — {', '.join(extra)}" if extra else "")
                )
        else:
            lines.append("- No active tasks.")
        lines.append("")

        open_decisions = [d for d in decisions if d["status"] == "open"]
        lines.append("## Open Decisions")
        if open_decisions:
            for decision in open_decisions[:10]:
                lines.append(
                    f"- {decision['question']} "
                    f"({self._decision_summary(decision)})"
                )
        else:
            lines.append("- No open consensus decisions.")
        lines.append("")

        lines.append("## Shared Skills")
        if skills:
            for skill in skills[:10]:
                lines.append(
                    f"- {skill['name']} (v{skill['version']}, {skill['uses']} uses) — "
                    f"{skill['description']}"
                )
        else:
            lines.append("- No shared skills yet.")
        lines.append("")

        lines.append("## Milestones")
        if state["milestones"]:
            for milestone in state["milestones"]:
                lines.append(
                    f"- {milestone['target']} "
                    f"(cycle {milestone['cycle']}, hit at {milestone['hit_at']})"
                )
        else:
            lines.append("- No milestones yet.")

        return "\n".join(lines) + "\n"

    def _render_task_queue_markdown(self, tasks: List[Dict[str, Any]]) -> str:
        status_meta = [
            ("Pending", "pending", "[ ]"),
            ("In Progress", "in_progress", "[~]"),
            ("Blocked", "blocked", "[!]"),
            ("Completed", "completed", "[x]"),
        ]
        lines = [
            "# Shared Task Queue",
            "",
            "> Auto-generated by ShareClaw. Any agent can read this mirror and act on it.",
            "",
        ]
        for heading, status, checkbox in status_meta:
            lines.append(f"## {heading}")
            matching = [task for task in tasks if task["status"] == status]
            if not matching:
                lines.append(f"- {heading.lower()} queue is empty.")
                lines.append("")
                continue

            for task in sorted(matching, key=self._task_sort_key):
                extras = [f"assigned: {task.get('assigned_to', 'any')}"]
                if task.get("deadline"):
                    extras.append(f"deadline: {task['deadline']}")
                if status == "in_progress" and task.get("started_at"):
                    extras.append(f"started: {task['started_at']}")
                if status == "completed" and task.get("completed_at"):
                    extras.append(f"completed: {task['completed_at']}")
                if status == "completed" and task.get("completed_by"):
                    extras.append(f"by: {task['completed_by']}")
                if status == "completed" and task.get("result"):
                    extras.append(f"result: {task['result']}")
                if status == "blocked" and task.get("note"):
                    extras.append(f"note: {task['note']}")
                details = task.get("details")
                line = (
                    f"- {checkbox} **[{task['priority']}]** {task['title']} — "
                    + " — ".join(extras)
                )
                lines.append(line)
                if details:
                    lines.append(f"  details: {details}")
            lines.append("")
        return "\n".join(lines) + "\n"

    def _render_events_markdown(self, events: List[Dict[str, Any]]) -> str:
        lines = [
            "# Agent Event Stream",
            "",
            "> Auto-generated by ShareClaw. Events are append-only and capped to the last 100 items.",
            "",
        ]
        if not events:
            lines.extend(["No events yet.", ""])
            return "\n".join(lines)

        for event in events[-50:]:
            lines.append(f"## {event['timestamp']} — {event['type']}")
            lines.append(f"**Agent:** {event['agent']}")
            if event.get("details"):
                lines.append(f"**Details:** {event['details']}")
            if event.get("data"):
                lines.append(f"**Data:** `{json.dumps(event['data'], sort_keys=True)}`")
            lines.append("")
        return "\n".join(lines)

    def _render_decisions_markdown(self, decisions: List[Dict[str, Any]]) -> str:
        lines = [
            "# Consensus Decisions",
            "",
            "> Auto-generated by ShareClaw. Open decisions are unresolved; resolved decisions preserve the vote trail.",
            "",
        ]
        open_decisions = [d for d in decisions if d["status"] == "open"]
        resolved_decisions = [d for d in decisions if d["status"] == "resolved"]

        lines.append("## Open")
        if open_decisions:
            for decision in open_decisions:
                lines.append(f"### {decision['question']}")
                lines.append(f"- id: {decision['id']}")
                if decision.get("context"):
                    lines.append(f"- context: {decision['context']}")
                if decision.get("options"):
                    lines.append(f"- options: {', '.join(decision['options'])}")
                lines.append(f"- votes: {self._decision_summary(decision)}")
                lines.append("")
        else:
            lines.extend(["No open decisions.", ""])

        lines.append("## Resolved")
        if resolved_decisions:
            for decision in resolved_decisions[-20:]:
                resolution = decision.get("resolution", {})
                lines.append(f"### {decision['question']}")
                lines.append(f"- winner: {resolution.get('winner', 'unknown')}")
                lines.append(f"- total votes: {resolution.get('total_votes', 0)}")
                lines.append(f"- summary: {resolution.get('summary', 'No summary')}")
                lines.append("")
        else:
            lines.extend(["No resolved decisions yet.", ""])

        return "\n".join(lines)

    def _sync_markdown_mirrors_unlocked(self):
        tasks = self._read_tasks_unlocked()
        decisions = self._read_decisions_unlocked()
        events = self._read_events_unlocked()
        skills = self._list_skills_unlocked()

        self.shared_brain_markdown_file.write_text(
            self._render_shared_brain_markdown(self.state, tasks, decisions, skills),
            encoding="utf-8",
        )
        self.task_queue_markdown_file.write_text(
            self._render_task_queue_markdown(tasks),
            encoding="utf-8",
        )
        self.events_markdown_file.write_text(
            self._render_events_markdown(events),
            encoding="utf-8",
        )
        self.decisions_markdown_file.write_text(
            self._render_decisions_markdown(decisions),
            encoding="utf-8",
        )

    # ── Targets ──────────────────────────────────────────────────

    def set_target(self, target: str, deadline: str = None):
        """Set the current cycle target. Must be specific and measurable."""
        with self._locked():
            self.state = self._load_state_unlocked()
            current_target = self._set_target_unlocked(target, deadline)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "TARGET_SET",
                {"target": target, "deadline": deadline, "cycle": current_target["cycle"]},
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"🎯 Cycle {self.state['cycle']} target: {target}")

    def hit_target(self):
        """Mark current target as achieved."""
        with self._locked():
            self.state = self._load_state_unlocked()
            if not self.state["current_target"]:
                return
            self.state["current_target"]["status"] = "hit"
            self.state["current_target"]["hit_at"] = self._now()
            self.state["milestones"].append(
                {
                    "target": self.state["current_target"]["target"],
                    "cycle": self.state["cycle"],
                    "hit_at": self._now(),
                }
            )
            self._save_state_unlocked()
            self._append_event_unlocked(
                "TARGET_HIT",
                {
                    "target": self.state["current_target"]["target"],
                    "cycle": self.state["cycle"],
                },
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"✅ TARGET HIT: {self.state['current_target']['target']}")

    def miss_target(self, reason: str):
        """Mark current target as missed with analysis."""
        with self._locked():
            self.state = self._load_state_unlocked()
            if not self.state["current_target"]:
                return
            self.state["current_target"]["status"] = "missed"
            self.state["current_target"]["reason"] = reason
            self._save_state_unlocked()
            self._append_event_unlocked(
                "TARGET_MISSED",
                {
                    "target": self.state["current_target"]["target"],
                    "reason": reason,
                    "cycle": self.state["cycle"],
                },
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"❌ Target missed: {reason}")

    def auto_target(self, current_value: float):
        """Automatically set the next target based on the configured step size."""
        metric = self.state.get("metric", "score")
        target_value = round(current_value * self.state.get("step_size", 1.5))
        self.set_target(f"{metric} ≥ {target_value} (current: {current_value})")
        return target_value

    def auto_advance(self, variable: str, variant: str, before: float, after: float):
        """Automatically decide advance or discard based on metric change."""
        status = "advance" if after > before else "discard"
        delta_pct = round((after - before) / max(before, 1) * 100, 1)
        desc = (
            f"{variant} {'improved' if status == 'advance' else 'worsened'} "
            f"{self.state.get('metric', 'score')} by {delta_pct}%"
        )
        self.log_cycle(variable, variant, before, after, status, desc)
        if status == "advance":
            self.learn(
                f"{variable}={variant} improves {self.state.get('metric', 'score')}",
                evidence=f"{before}→{after} ({delta_pct:+.1f}%)",
            )
        else:
            self.fail(
                f"{variable}={variant}",
                reason=f"{self.state.get('metric', 'score')} went {before}→{after} ({delta_pct:+.1f}%)",
            )
        return status

    def next_variable(self) -> tuple:
        """Suggest the next variable that does not have a winning variant yet."""
        with self._locked():
            self.state = self._load_state_unlocked()
            tested = self.state.get("variable_results", {})
            variables = self.state.get("variables", [])
            for variable in variables:
                if variable not in tested:
                    return variable, "first variant"
            return None, None

    def winning_combo(self) -> dict:
        """Return the current best combination of tested variables."""
        with self._locked():
            self.state = self._load_state_unlocked()
            return deepcopy(self.state.get("variable_results", {}))

    # ── Learning ─────────────────────────────────────────────────

    def learn(self, what: str, evidence: str):
        """Record something that works. Requires evidence."""
        with self._locked():
            self.state = self._load_state_unlocked()
            self._learn_unlocked(what, evidence)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "LEARNING_RECORDED",
                {"what": what, "evidence": evidence, "cycle": self.state["cycle"]},
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"📗 Learned: {what}")

    def fail(self, what: str, reason: str):
        """Record something that doesn't work. Never deleted."""
        with self._locked():
            self.state = self._load_state_unlocked()
            self._fail_unlocked(what, reason)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "FAILURE_RECORDED",
                {"what": what, "reason": reason, "cycle": self.state["cycle"]},
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"📕 Failed: {what} — {reason}")

    # ── Cycle Logging ────────────────────────────────────────────

    def log_cycle(
        self,
        variable: str,
        variant: str,
        before: float,
        after: float,
        status: str,
        description: str = "",
    ):
        """Log one experiment cycle. Status: 'advance' or 'discard'."""
        with self._locked():
            self.state = self._load_state_unlocked()
            cycle = self._log_cycle_unlocked(variable, variant, before, after, status, description)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "CYCLE_LOGGED",
                {
                    "cycle": cycle["cycle"],
                    "variable": variable,
                    "variant": variant,
                    "status": status,
                    "after": after,
                },
            )
            self._sync_markdown_mirrors_unlocked()

        icon = "✅" if status == "advance" else "❌"
        print(
            f"{icon} Cycle {cycle['cycle']}: {variable}={variant} → "
            f"{before}→{after} ({cycle['delta_pct']:+.1f}%) [{status}]"
        )

    def introspect(
        self,
        expected: str,
        actual: str,
        why: str,
        next_action: str,
        next_target: str,
    ):
        """Record cycle introspection — the 5 questions."""
        with self._locked():
            self.state = self._load_state_unlocked()
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
                self._save_state_unlocked()
                self._append_event_unlocked(
                    "INTROSPECTION_RECORDED",
                    {"cycle": self.state["cycle"], "next_target": next_target},
                )
                self._sync_markdown_mirrors_unlocked()
        print(f"🔍 Introspection logged for cycle {self.state['cycle']}")

    # ── Skills ───────────────────────────────────────────────────

    def add_skill(
        self,
        name: str,
        description: str,
        formula: str = "",
        examples_good: Optional[List[str]] = None,
        examples_bad: Optional[List[str]] = None,
        code: str = "",
        created_by: str = "unknown",
    ):
        """Share or update a skill that other agents can use."""
        with self._locked():
            self.state = self._load_state_unlocked()
            skill_file = self.skills_dir / f"{name}.json"
            previous = self._read_json_unlocked(skill_file, {})
            version = int(previous.get("version", 0)) + 1
            uses = int(previous.get("uses", 0))
            skill = {
                "name": name,
                "description": description,
                "formula": formula,
                "examples_good": examples_good or [],
                "examples_bad": examples_bad or [],
                "code": code,
                "created_by": created_by,
                "created_at": previous.get("created_at", self._now()),
                "updated_at": self._now(),
                "version": version,
                "uses": uses,
            }
            self._write_json_unlocked(skill_file, skill)
            if name not in self.state["skills"]:
                self.state["skills"].append(name)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "SKILL_SHARED" if version == 1 else "SKILL_UPDATED",
                {"name": name, "version": version},
                agent=created_by,
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"🔧 Skill shared: {name} (v{version})")

    def get_skill(self, name: str) -> dict:
        """Read a shared skill."""
        with self._locked():
            skill_file = self.skills_dir / f"{name}.json"
            if not skill_file.exists():
                return {}
            skill = self._read_json_unlocked(skill_file, {})
            skill["uses"] = int(skill.get("uses", 0)) + 1
            skill["updated_at"] = self._now()
            self._write_json_unlocked(skill_file, skill)
            self._sync_markdown_mirrors_unlocked()
            return skill

    def list_skills(self) -> list:
        """List all shared skills."""
        with self._locked():
            return self._list_skills_unlocked()

    # ── Handoffs ─────────────────────────────────────────────────

    def handoff(
        self,
        to_agent: str,
        task: str,
        context: str = "",
        files: Optional[List[str]] = None,
        from_agent: str = "unknown",
    ):
        """Create a handoff for another agent."""
        with self._locked():
            self.state = self._load_state_unlocked()
            handoff = {
                "id": self._new_id("handoff"),
                "from": from_agent,
                "to": to_agent,
                "task": task,
                "context": context,
                "files": files or [],
                "status": "ready",
                "created_at": self._now(),
            }
            handoff_file = self.handoffs_dir / f"{handoff['id']}.json"
            self._write_json_unlocked(handoff_file, handoff)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "HANDOFF_CREATED",
                {"handoff_id": handoff["id"], "task": task, "to": to_agent},
                agent=from_agent,
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"📤 Handoff created: {task} → {to_agent}")
        return handoff["id"]

    def pickup_handoff(self, agent_name: str) -> dict:
        """Pick up the next available handoff for this agent."""
        with self._locked():
            self.state = self._load_state_unlocked()
            for path in sorted(self.handoffs_dir.glob("*.json")):
                handoff = self._read_json_unlocked(path, {})
                if handoff.get("status") != "ready":
                    continue
                if handoff.get("to") not in {agent_name, "any"}:
                    continue
                handoff["status"] = "picked_up"
                handoff["picked_up_at"] = self._now()
                handoff["picked_up_by"] = agent_name
                self._write_json_unlocked(path, handoff)
                self._save_state_unlocked()
                self._append_event_unlocked(
                    "HANDOFF_PICKED_UP",
                    {"handoff_id": handoff["id"], "task": handoff["task"]},
                    agent=agent_name,
                )
                self._sync_markdown_mirrors_unlocked()
                print(f"📥 Picked up: {handoff['task']}")
                return handoff
            return {}

    def complete_handoff(self, handoff_id: str, result: str):
        """Mark a handoff as completed."""
        with self._locked():
            self.state = self._load_state_unlocked()
            handoff_file = self.handoffs_dir / f"{handoff_id}.json"
            if not handoff_file.exists():
                return
            handoff = self._read_json_unlocked(handoff_file, {})
            handoff["status"] = "completed"
            handoff["result"] = result
            handoff["completed_at"] = self._now()
            self._write_json_unlocked(handoff_file, handoff)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "HANDOFF_COMPLETED",
                {"handoff_id": handoff_id, "task": handoff.get("task"), "result": result},
                agent=handoff.get("picked_up_by", handoff.get("to", "unknown")),
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"✅ Handoff completed: {handoff.get('task', handoff_id)}")

    # ── Events ───────────────────────────────────────────────────

    def emit(self, event_type: str, data: dict = None, agent: str = "unknown", details: str = ""):
        """Publish an event to the append-only event stream."""
        with self._locked():
            self.state = self._load_state_unlocked()
            self._append_event_unlocked(event_type, data, agent=agent, details=details)
            self._save_state_unlocked()
            self._sync_markdown_mirrors_unlocked()

    def get_events(self, event_type: str = None, limit: int = 10) -> list:
        """Get recent events, optionally filtered by type."""
        with self._locked():
            events = self._read_events_unlocked()
            if event_type:
                events = [event for event in events if event["type"] == event_type]
            return events[-limit:]

    # ── Task Queue ───────────────────────────────────────────────

    def create_task(
        self,
        title: str,
        priority: str = "MED",
        assigned_to: str = "any",
        deadline: Optional[str] = None,
        details: str = "",
        created_by: str = "unknown",
    ) -> str:
        """Create a queue item that any agent can later pick up."""
        with self._locked():
            self.state = self._load_state_unlocked()
            tasks = self._read_tasks_unlocked()
            task = {
                "id": self._new_id("task"),
                "title": title,
                "details": details,
                "priority": self._normalize_priority(priority),
                "assigned_to": assigned_to,
                "created_by": created_by,
                "status": "pending",
                "created_at": self._now(),
                "deadline": deadline,
            }
            tasks.append(task)
            self._write_tasks_unlocked(tasks)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "TASK_CREATED",
                {"task_id": task["id"], "title": title, "priority": task["priority"]},
                agent=created_by,
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"📝 Task created: {title}")
        return task["id"]

    def get_task(self, task_id: str) -> dict:
        """Return a single task by id."""
        with self._locked():
            tasks = self._read_tasks_unlocked()
            for task in tasks:
                if task["id"] == task_id:
                    return task
            return {}

    def list_tasks(
        self,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        priority: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list:
        """List tasks filtered by status, assignee, or priority."""
        with self._locked():
            tasks = self._read_tasks_unlocked()
            if status:
                tasks = [task for task in tasks if task["status"] == status]
            if assigned_to:
                tasks = [task for task in tasks if task.get("assigned_to") == assigned_to]
            if priority:
                normalized = self._normalize_priority(priority)
                tasks = [task for task in tasks if task.get("priority") == normalized]
            tasks = sorted(tasks, key=self._task_sort_key)
            if limit is not None:
                tasks = tasks[:limit]
            return tasks

    def pickup_task(self, agent_name: str, task_id: Optional[str] = None) -> dict:
        """Pick up a pending task, preferring highest priority first."""
        with self._locked():
            self.state = self._load_state_unlocked()
            tasks = self._read_tasks_unlocked()
            candidates = []
            for task in tasks:
                if task["status"] != "pending":
                    continue
                if task.get("assigned_to") not in {"any", agent_name}:
                    continue
                if task_id and task["id"] != task_id:
                    continue
                candidates.append(task)

            if not candidates:
                return {}

            chosen = sorted(candidates, key=self._task_sort_key)[0]
            chosen["status"] = "in_progress"
            chosen["assigned_to"] = agent_name
            chosen["started_at"] = self._now()
            self._write_tasks_unlocked(tasks)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "TASK_PICKED_UP",
                {"task_id": chosen["id"], "title": chosen["title"]},
                agent=agent_name,
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"📥 Task picked up: {chosen['title']}")
        return chosen

    def complete_task(self, task_id: str, result: str, completed_by: str = "unknown") -> dict:
        """Mark a task as completed."""
        with self._locked():
            self.state = self._load_state_unlocked()
            tasks = self._read_tasks_unlocked()
            for task in tasks:
                if task["id"] != task_id:
                    continue
                task["status"] = "completed"
                task["result"] = result
                task["completed_at"] = self._now()
                task["completed_by"] = completed_by
                if not task.get("assigned_to") or task["assigned_to"] == "any":
                    task["assigned_to"] = completed_by
                self._write_tasks_unlocked(tasks)
                self._save_state_unlocked()
                self._append_event_unlocked(
                    "TASK_COMPLETED",
                    {"task_id": task_id, "title": task["title"], "result": result},
                    agent=completed_by,
                )
                self._sync_markdown_mirrors_unlocked()
                print(f"✅ Task completed: {task['title']}")
                return task
            return {}

    def requeue_task(
        self,
        task_id: str,
        note: str = "",
        assigned_to: str = "any",
        status: str = "pending",
    ) -> dict:
        """Move a task back into the queue, optionally as blocked."""
        if status not in {"pending", "blocked"}:
            raise ValueError("status must be 'pending' or 'blocked'")

        with self._locked():
            self.state = self._load_state_unlocked()
            tasks = self._read_tasks_unlocked()
            for task in tasks:
                if task["id"] != task_id:
                    continue
                task["status"] = status
                task["assigned_to"] = assigned_to
                task["note"] = note
                task["requeued_at"] = self._now()
                task.pop("started_at", None)
                self._write_tasks_unlocked(tasks)
                self._save_state_unlocked()
                self._append_event_unlocked(
                    "TASK_REQUEUED" if status == "pending" else "TASK_BLOCKED",
                    {"task_id": task_id, "title": task["title"], "note": note},
                )
                self._sync_markdown_mirrors_unlocked()
                print(f"🔁 Task moved to {status}: {task['title']}")
                return task
            return {}

    # ── Consensus ────────────────────────────────────────────────

    def start_consensus(
        self,
        question: str,
        options: Optional[List[str]] = None,
        created_by: str = "unknown",
        context: str = "",
        default_policy: str = "keep_current",
    ) -> str:
        """Open a consensus decision for agents to vote on."""
        with self._locked():
            self.state = self._load_state_unlocked()
            decisions = self._read_decisions_unlocked()
            decision = {
                "id": self._new_id("decision"),
                "question": question,
                "options": options or ["YES", "NO"],
                "context": context,
                "created_by": created_by,
                "created_at": self._now(),
                "default_policy": default_policy,
                "status": "open",
                "votes": [],
                "resolution": None,
            }
            decisions.append(decision)
            self._write_decisions_unlocked(decisions)
            self._save_state_unlocked()
            self._append_event_unlocked(
                "CONSENSUS_STARTED",
                {"decision_id": decision["id"], "question": question},
                agent=created_by,
            )
            self._sync_markdown_mirrors_unlocked()
        print(f"🗳️ Consensus started: {question}")
        return decision["id"]

    def list_decisions(self, status: Optional[str] = None, limit: Optional[int] = None) -> list:
        """List consensus decisions, optionally filtered by status."""
        with self._locked():
            decisions = self._read_decisions_unlocked()
            if status:
                decisions = [decision for decision in decisions if decision["status"] == status]
            decisions = sorted(
                decisions,
                key=lambda decision: (decision["status"] != "open", decision["created_at"]),
            )
            if limit is not None:
                decisions = decisions[:limit]
            return decisions

    def get_decision(self, decision_id: str) -> dict:
        """Return one consensus decision."""
        with self._locked():
            decisions = self._read_decisions_unlocked()
            for decision in decisions:
                if decision["id"] == decision_id:
                    return decision
            return {}

    def vote(
        self,
        decision_id: str,
        agent: str,
        choice: str,
        reason: str,
        data: str = "",
        confidence: Optional[float] = None,
    ) -> dict:
        """Cast or update an agent's vote on an open decision."""
        with self._locked():
            self.state = self._load_state_unlocked()
            decisions = self._read_decisions_unlocked()
            for decision in decisions:
                if decision["id"] != decision_id:
                    continue
                if decision["status"] != "open":
                    return {}
                normalized_choice = self._normalize_choice(decision.get("options", []), choice)
                if decision.get("options") and normalized_choice not in decision["options"]:
                    raise ValueError(
                        f"choice must be one of: {', '.join(decision['options'])}"
                    )

                votes = [vote for vote in decision.get("votes", []) if vote["agent"] != agent]
                votes.append(
                    {
                        "agent": agent,
                        "choice": normalized_choice,
                        "reason": reason,
                        "data": data,
                        "confidence": confidence,
                        "voted_at": self._now(),
                    }
                )
                decision["votes"] = votes
                self._write_decisions_unlocked(decisions)
                self._save_state_unlocked()
                self._append_event_unlocked(
                    "CONSENSUS_VOTE",
                    {
                        "decision_id": decision_id,
                        "question": decision["question"],
                        "choice": normalized_choice,
                    },
                    agent=agent,
                )
                self._sync_markdown_mirrors_unlocked()
                print(f"🗳️ Vote recorded: {agent} → {normalized_choice}")
                return decision
            return {}

    def resolve_consensus(self, decision_id: str, resolved_by: str = "system") -> dict:
        """Resolve a consensus decision using majority vote and a fallback tie policy."""
        with self._locked():
            self.state = self._load_state_unlocked()
            decisions = self._read_decisions_unlocked()
            for decision in decisions:
                if decision["id"] != decision_id:
                    continue
                if decision["status"] == "resolved":
                    return decision

                counts = self._decision_counts(decision)
                total_votes = sum(counts.values())
                winner = self._fallback_choice(decision)
                tie = False

                if counts:
                    top = counts.most_common()
                    winner = top[0][0]
                    if len(top) > 1 and top[0][1] == top[1][1]:
                        tie = True
                        winner = self._fallback_choice(decision)

                summary = (
                    f"Tie resolved via {decision.get('default_policy', 'keep_current')}"
                    if tie
                    else f"Majority winner: {winner}"
                )
                if total_votes == 0:
                    summary = f"No votes recorded. Fallback winner: {winner}"

                decision["status"] = "resolved"
                decision["resolution"] = {
                    "winner": winner,
                    "vote_counts": dict(counts),
                    "total_votes": total_votes,
                    "tie": tie,
                    "resolved_by": resolved_by,
                    "resolved_at": self._now(),
                    "summary": summary,
                }
                self._write_decisions_unlocked(decisions)
                self._save_state_unlocked()
                self._append_event_unlocked(
                    "CONSENSUS_RESOLVED",
                    {
                        "decision_id": decision_id,
                        "question": decision["question"],
                        "winner": winner,
                        "tie": tie,
                    },
                    agent=resolved_by,
                )
                self._sync_markdown_mirrors_unlocked()
                print(f"✅ Consensus resolved: {winner}")
                return decision
            return {}

    # ── Reporting ────────────────────────────────────────────────

    def report(self) -> str:
        """Generate a status report with learning, queue, and decision state."""
        with self._locked():
            self.state = self._load_state_unlocked()
            tasks = self._read_tasks_unlocked()
            decisions = self._read_decisions_unlocked()
            skills = self._list_skills_unlocked()
            events = self._read_events_unlocked()

            s = self.state
            lines = []
            lines.append(f"\n{'=' * 62}")
            lines.append(f"  🦞🧠 SHARECLAW — {s['project']}")
            lines.append(
                f"  Metric: {s.get('metric', 'score')} | Cycle {s['cycle']} | "
                f"{len(s['works'])} wins | {len(s['fails'])} fails"
            )
            if s.get("objective"):
                lines.append(f"  Objective: {s['objective']}")
            lines.append(f"{'=' * 62}\n")

            target = s.get("current_target")
            if target:
                icon = {"active": "🎯", "hit": "✅", "missed": "❌"}.get(target["status"], "❓")
                lines.append(f"  {icon} Target: {target['target']} [{target['status']}]")
                if target.get("deadline"):
                    lines.append(f"     Deadline: {target['deadline']}")
                lines.append("")

            if s.get("history"):
                lines.append("  📈 Progress:")
                metrics = [point["metric"] for point in s["history"][-20:]]
                max_metric = max(metrics) if metrics else 1
                for idx, metric in enumerate(metrics, start=1):
                    bar = "█" * int(metric / max(max_metric, 1) * 30)
                    lines.append(f"    {idx:3d} │ {bar} {metric}")
                lines.append("")

            if s["works"]:
                lines.append("  📗 What Works:")
                for item in s["works"][-5:]:
                    lines.append(f"    ✓ {item['what']}")
                lines.append("")

            if s["fails"]:
                lines.append("  📕 What Doesn't:")
                for item in s["fails"][-5:]:
                    lines.append(f"    ✗ {item['what']} — {item['reason']}")
                lines.append("")

            active_tasks = [task for task in tasks if task["status"] in {"pending", "in_progress", "blocked"}]
            if active_tasks:
                lines.append("  🗂️ Active Tasks:")
                for task in sorted(active_tasks, key=self._task_sort_key)[:5]:
                    lines.append(
                        f"    [{task['status']}] [{task['priority']}] {task['title']} "
                        f"→ {task.get('assigned_to', 'any')}"
                    )
                lines.append("")

            open_decisions = [decision for decision in decisions if decision["status"] == "open"]
            if open_decisions:
                lines.append("  🗳️ Open Decisions:")
                for decision in open_decisions[:5]:
                    lines.append(
                        f"    • {decision['question']} "
                        f"({self._decision_summary(decision)})"
                    )
                lines.append("")

            if s["cycles"]:
                lines.append("  🔄 Recent Cycles:")
                for cycle in s["cycles"][-5:]:
                    icon = "✅" if cycle["status"] == "advance" else "❌"
                    lines.append(
                        f"    {icon} #{cycle['cycle']}: {cycle['variable']}={cycle['variant']} "
                        f"→ {cycle['before']}→{cycle['after']} ({cycle['delta_pct']:+.1f}%)"
                    )
                lines.append("")

            if skills:
                lines.append("  🔧 Shared Skills:")
                for skill in skills[:5]:
                    lines.append(
                        f"    • {skill['name']} (v{skill['version']}, {skill['uses']} uses)"
                    )
                lines.append("")

            if events:
                lines.append("  📡 Recent Events:")
                for event in events[-5:]:
                    lines.append(f"    • {event['type']} by {event['agent']}")
                lines.append("")

            if s.get("milestones"):
                lines.append("  🏆 Milestones:")
                for milestone in s["milestones"][-5:]:
                    lines.append(f"    ★ {milestone['target']} (cycle {milestone['cycle']})")
                lines.append("")

            lines.append(f"{'=' * 62}\n")
            report_text = "\n".join(lines)

        print(report_text)
        return report_text

    # ── Context for LLM agents ───────────────────────────────────

    def context(self) -> str:
        """Generate a compact context string for agent prompts."""
        with self._locked():
            self.state = self._load_state_unlocked()
            tasks = self._read_tasks_unlocked()
            decisions = self._read_decisions_unlocked()
            skills = self._list_skills_unlocked()
            events = self._read_events_unlocked()

            s = self.state
            ctx = [
                f"# ShareClaw Context — {s['project']}",
                f"Cycle: {s['cycle']}",
                f"Metric: {s.get('metric', 'score')}",
                f"Objective: {s.get('objective') or 'Not set'}",
            ]

            target = s.get("current_target")
            if target:
                ctx.append(
                    f"\n## Current Target\n{target['target']} "
                    f"[{target['status']}]"
                )

            if s["works"]:
                ctx.append("\n## What Works")
                for item in s["works"][-10:]:
                    ctx.append(f"- {item['what']} (evidence: {item['evidence']})")

            if s["fails"]:
                ctx.append("\n## What Doesn't Work (never repeat these)")
                for item in s["fails"][-10:]:
                    ctx.append(f"- {item['what']} — {item['reason']}")

            if s.get("variable_results"):
                ctx.append("\n## Winning Combo")
                for variable, result in s["variable_results"].items():
                    ctx.append(
                        f"- {variable}: {result['winner']} "
                        f"(value: {result['value']}, cycle: {result['cycle']})"
                    )

            active_tasks = [task for task in tasks if task["status"] in {"pending", "in_progress", "blocked"}]
            if active_tasks:
                ctx.append("\n## Active Task Queue")
                for task in sorted(active_tasks, key=self._task_sort_key)[:8]:
                    ctx.append(
                        f"- [{task['status']}] [{task['priority']}] {task['title']} "
                        f"(assigned: {task.get('assigned_to', 'any')})"
                    )

            open_decisions = [decision for decision in decisions if decision["status"] == "open"]
            if open_decisions:
                ctx.append("\n## Open Decisions")
                for decision in open_decisions[:8]:
                    ctx.append(
                        f"- {decision['question']} "
                        f"(votes: {self._decision_summary(decision)})"
                    )

            if s["cycles"]:
                ctx.append("\n## Last 3 Cycles")
                for cycle in s["cycles"][-3:]:
                    ctx.append(
                        f"- Cycle {cycle['cycle']}: {cycle['variable']}={cycle['variant']} "
                        f"→ {cycle['before']}→{cycle['after']} [{cycle['status']}]"
                    )

            if skills:
                ctx.append("\n## Available Skills")
                for skill in skills[:10]:
                    ctx.append(f"- {skill['name']}: {skill['description']}")

            if events:
                ctx.append("\n## Recent Events")
                for event in events[-5:]:
                    ctx.append(
                        f"- {event['timestamp']}: {event['type']} by {event['agent']}"
                    )

            return "\n".join(ctx)
