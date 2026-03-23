#!/usr/bin/env python3
"""ShareClaw CLI — manage a shared brain from the command line."""

import argparse
import json
from pathlib import Path

from .core import Brain


def _load_brain() -> Brain:
    brain_path = Path.cwd() / ".shareclaw" / "brain.json"
    if not brain_path.exists():
        raise SystemExit("⚠️  No ShareClaw brain found. Run: shareclaw init <project-name>")
    return Brain("default")


def _parse_json_blob(blob: str):
    try:
        return json.loads(blob)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON for --data: {exc}") from exc


def _print_files(brain: Brain):
    for name, path in brain.files().items():
        print(f"{name}: {path}")


def _print_tasks(tasks):
    if not tasks:
        print("No tasks found.")
        return
    for task in tasks:
        suffix = []
        if task.get("assigned_to"):
            suffix.append(f"assigned={task['assigned_to']}")
        if task.get("deadline"):
            suffix.append(f"deadline={task['deadline']}")
        if task.get("result"):
            suffix.append(f"result={task['result']}")
        print(
            f"{task['id']} [{task['status']}] [{task['priority']}] {task['title']}"
            + (f" — {', '.join(suffix)}" if suffix else "")
        )


def _print_decisions(decisions):
    if not decisions:
        print("No decisions found.")
        return
    for decision in decisions:
        resolution = ""
        if decision.get("resolution"):
            resolution = f" — winner={decision['resolution']['winner']}"
        print(f"{decision['id']} [{decision['status']}] {decision['question']}{resolution}")


def main():
    parser = argparse.ArgumentParser(
        description="🧠 ShareClaw — shared memory + self-improving coordination for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shareclaw init launch-swarm --objective "Grow awareness" --metric signups
  shareclaw target "50 signups/day"
  shareclaw cycle hook outrage 200 480 advance "outrage hook won"
  shareclaw task add "Ship demo video" --priority HIGH --by strategist
  shareclaw task pickup creator
  shareclaw consensus start "Switch hooks?" --option YES --option NO
  shareclaw consensus vote decision_123 heisenberg NO "Ragebait is still winning"
  shareclaw event emit TARGET_HIT --agent rutherford --data '{"views": 520}'
  shareclaw files
        """,
    )

    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("init", help="Initialize a new shared brain in ./.shareclaw")
    p.add_argument("project", help="Project name")
    p.add_argument("--objective", default="", help="What the system is trying to achieve")
    p.add_argument("--metric", default="score", help="Primary tracked metric")
    p.add_argument("--variables", nargs="*", default=None, help="Variables to test in order")
    p.add_argument("--wait-time", default="6 hours", help="Typical wait time between cycles")
    p.add_argument("--step-size", type=float, default=1.5, help="Target multiplier on success")

    p = sub.add_parser("target", help="Set cycle target")
    p.add_argument("target", help="Target description (be specific)")
    p.add_argument("--deadline", help="Deadline")

    p = sub.add_parser("learn", help="Record what works")
    p.add_argument("what", help="What works")
    p.add_argument("evidence", help="Evidence or data")

    p = sub.add_parser("fail", help="Record what doesn't work")
    p.add_argument("what", help="What failed")
    p.add_argument("reason", help="Why it failed")

    p = sub.add_parser("cycle", help="Log an experiment cycle")
    p.add_argument("variable", help="Variable tested")
    p.add_argument("variant", help="Variant used")
    p.add_argument("before", type=float, help="Metric before")
    p.add_argument("after", type=float, help="Metric after")
    p.add_argument("status", choices=["advance", "discard"], help="Result")
    p.add_argument("description", nargs="?", default="", help="Description")

    p = sub.add_parser("skill", help="Manage shared skills")
    p.add_argument("action", choices=["add", "list", "get"])
    p.add_argument("name", nargs="?", help="Skill name")
    p.add_argument("--description", help="Skill description")
    p.add_argument("--formula", default="", help="How the skill works")
    p.add_argument("--code", default="", help="Optional code snippet")
    p.add_argument("--by", default="unknown", help="Created by")

    p = sub.add_parser("handoff", help="Create a handoff for another agent")
    p.add_argument("to", help="Target agent")
    p.add_argument("task", help="Task description")
    p.add_argument("--context", default="", help="Extra context")
    p.add_argument("--file", action="append", dest="files", default=None, help="Related file path")
    p.add_argument("--from-agent", default="unknown", help="Agent creating the handoff")

    p = sub.add_parser("task", help="Manage the shared task queue")
    p.add_argument("action", choices=["add", "list", "get", "pickup", "done", "requeue"])
    p.add_argument("arg1", nargs="?", help="Action-specific argument")
    p.add_argument("arg2", nargs="?", help="Action-specific argument")
    p.add_argument("--priority", help="Task priority: HIGH, MED, LOW")
    p.add_argument("--assigned", default="any", help="Assigned agent (default: any)")
    p.add_argument("--deadline", help="Task deadline")
    p.add_argument("--details", default="", help="Extra task details")
    p.add_argument("--by", default="unknown", help="Agent or human performing the action")
    p.add_argument("--status", help="Filter status when listing")
    p.add_argument("--limit", type=int, help="Max tasks to print")
    p.add_argument("--blocked", action="store_true", help="Requeue as blocked instead of pending")
    p.add_argument("--note", default="", help="Reason for requeue/block")

    p = sub.add_parser("consensus", help="Manage consensus decisions")
    p.add_argument("action", choices=["start", "list", "get", "vote", "resolve"])
    p.add_argument("arg1", nargs="?", help="Action-specific argument")
    p.add_argument("arg2", nargs="?", help="Action-specific argument")
    p.add_argument("arg3", nargs="?", help="Action-specific argument")
    p.add_argument("arg4", nargs="?", help="Action-specific argument")
    p.add_argument("--option", action="append", dest="options", default=None, help="Allowed option")
    p.add_argument("--context", default="", help="Decision context")
    p.add_argument("--policy", default="keep_current", help="Tie fallback policy")
    p.add_argument("--data", default="", help="Supporting data for a vote")
    p.add_argument("--confidence", type=float, help="Optional confidence score")
    p.add_argument("--by", default="unknown", help="Agent or human performing the action")
    p.add_argument("--status", help="Filter status when listing")
    p.add_argument("--limit", type=int, help="Max decisions to print")

    p = sub.add_parser("event", help="Emit or list events")
    p.add_argument("action", choices=["emit", "list"])
    p.add_argument("type", nargs="?", help="Event type")
    p.add_argument("--agent", default="unknown", help="Agent publishing the event")
    p.add_argument("--data", default="{}", help="JSON payload for event emit")
    p.add_argument("--details", default="", help="Human-readable event details")
    p.add_argument("--limit", type=int, default=10, help="Max events to show")

    sub.add_parser("status", help="Show current system report")
    sub.add_parser("context", help="Print context for agent prompts")
    sub.add_parser("files", help="Print key runtime file paths")
    sub.add_parser("hit", help="Mark target as achieved")

    p = sub.add_parser("miss", help="Mark target as missed")
    p.add_argument("reason", help="Why it was missed")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "init":
        brain = Brain(
            args.project,
            objective=args.objective,
            metric=args.metric,
            variables=args.variables,
            wait_time=args.wait_time,
            step_size=args.step_size,
        )
        with brain._locked():
            brain.state = brain._load_state_unlocked()
            brain._save_state_unlocked()
            brain._sync_markdown_mirrors_unlocked()
        print(f"🧠 ShareClaw initialized: {args.project}")
        _print_files(brain)
        return

    brain = _load_brain()

    if args.command == "target":
        brain.set_target(args.target, args.deadline)

    elif args.command == "learn":
        brain.learn(args.what, args.evidence)

    elif args.command == "fail":
        brain.fail(args.what, args.reason)

    elif args.command == "cycle":
        brain.log_cycle(
            args.variable,
            args.variant,
            args.before,
            args.after,
            args.status,
            args.description,
        )

    elif args.command == "skill":
        if args.action == "add":
            brain.add_skill(
                args.name,
                args.description or "",
                formula=args.formula,
                code=args.code,
                created_by=args.by,
            )
        elif args.action == "list":
            skills = brain.list_skills()
            if not skills:
                print("No skills found.")
            for skill in skills:
                print(
                    f"{skill['name']} (v{skill['version']}, {skill['uses']} uses) — "
                    f"{skill['description']}"
                )
        elif args.action == "get":
            skill = brain.get_skill(args.name)
            if not skill:
                print("Skill not found.")
            else:
                print(json.dumps(skill, indent=2))

    elif args.command == "handoff":
        brain.handoff(
            args.to,
            args.task,
            context=args.context,
            files=args.files,
            from_agent=args.from_agent,
        )

    elif args.command == "task":
        if args.action == "add":
            if not args.arg1:
                raise SystemExit("task add requires a title")
            brain.create_task(
                args.arg1,
                priority=args.priority or "MED",
                assigned_to=args.assigned,
                deadline=args.deadline,
                details=args.details,
                created_by=args.by,
            )
        elif args.action == "list":
            tasks = brain.list_tasks(
                status=args.status,
                assigned_to=None if args.assigned == "any" else args.assigned,
                priority=args.priority,
                limit=args.limit,
            )
            _print_tasks(tasks)
        elif args.action == "get":
            if not args.arg1:
                raise SystemExit("task get requires a task id")
            print(json.dumps(brain.get_task(args.arg1), indent=2))
        elif args.action == "pickup":
            if not args.arg1:
                raise SystemExit("task pickup requires an agent name")
            task = brain.pickup_task(args.arg1, task_id=args.arg2)
            print(json.dumps(task, indent=2))
        elif args.action == "done":
            if not args.arg1 or not args.arg2:
                raise SystemExit("task done requires a task id and result")
            task = brain.complete_task(args.arg1, args.arg2, completed_by=args.by)
            print(json.dumps(task, indent=2))
        elif args.action == "requeue":
            if not args.arg1:
                raise SystemExit("task requeue requires a task id")
            task = brain.requeue_task(
                args.arg1,
                note=args.note,
                assigned_to=args.assigned,
                status="blocked" if args.blocked else "pending",
            )
            print(json.dumps(task, indent=2))

    elif args.command == "consensus":
        if args.action == "start":
            if not args.arg1:
                raise SystemExit("consensus start requires a question")
            brain.start_consensus(
                args.arg1,
                options=args.options,
                created_by=args.by,
                context=args.context,
                default_policy=args.policy,
            )
        elif args.action == "list":
            _print_decisions(brain.list_decisions(status=args.status, limit=args.limit))
        elif args.action == "get":
            if not args.arg1:
                raise SystemExit("consensus get requires a decision id")
            print(json.dumps(brain.get_decision(args.arg1), indent=2))
        elif args.action == "vote":
            if not all([args.arg1, args.arg2, args.arg3, args.arg4]):
                raise SystemExit("consensus vote requires id, agent, choice, and reason")
            decision = brain.vote(
                args.arg1,
                args.arg2,
                args.arg3,
                args.arg4,
                data=args.data,
                confidence=args.confidence,
            )
            print(json.dumps(decision, indent=2))
        elif args.action == "resolve":
            if not args.arg1:
                raise SystemExit("consensus resolve requires a decision id")
            print(json.dumps(brain.resolve_consensus(args.arg1, resolved_by=args.by), indent=2))

    elif args.command == "event":
        if args.action == "emit":
            if not args.type:
                raise SystemExit("event emit requires an event type")
            brain.emit(
                args.type,
                data=_parse_json_blob(args.data),
                agent=args.agent,
                details=args.details,
            )
        else:
            events = brain.get_events(event_type=args.type, limit=args.limit)
            print(json.dumps(events, indent=2))

    elif args.command == "status":
        brain.report()

    elif args.command == "context":
        print(brain.context())

    elif args.command == "files":
        _print_files(brain)

    elif args.command == "hit":
        brain.hit_target()

    elif args.command == "miss":
        brain.miss_target(args.reason)


if __name__ == "__main__":
    main()
