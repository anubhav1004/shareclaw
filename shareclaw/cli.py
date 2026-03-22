#!/usr/bin/env python3
"""ShareClaw CLI — manage your shared brain from the command line."""

import argparse
import sys
from .core import Brain


def main():
    parser = argparse.ArgumentParser(
        description="🧠 ShareClaw — Shared memory for multi-agent AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shareclaw init my-project              Initialize a new shared brain
  shareclaw target "500 views/post"      Set a target for current cycle
  shareclaw learn "ragebait works" "2x more views in cycle 1"
  shareclaw fail "long hooks" "200 views, no engagement"
  shareclaw cycle hook_style ragebait 200 450 advance "ragebait won"
  shareclaw skill add my-skill "Does cool things"
  shareclaw handoff agent-b "Post these videos"
  shareclaw status                       Show current state
  shareclaw context                      Print context for LLM agents
        """)

    sub = parser.add_subparsers(dest="command")

    # init
    p = sub.add_parser("init", help="Initialize shared brain")
    p.add_argument("project", help="Project name")

    # target
    p = sub.add_parser("target", help="Set cycle target")
    p.add_argument("target", help="Target description (be specific)")
    p.add_argument("--deadline", help="Deadline")

    # learn
    p = sub.add_parser("learn", help="Record what works")
    p.add_argument("what", help="What works")
    p.add_argument("evidence", help="Evidence/data")

    # fail
    p = sub.add_parser("fail", help="Record what doesn't work")
    p.add_argument("what", help="What failed")
    p.add_argument("reason", help="Why it failed")

    # cycle
    p = sub.add_parser("cycle", help="Log an experiment cycle")
    p.add_argument("variable", help="Variable tested")
    p.add_argument("variant", help="Variant used")
    p.add_argument("before", type=float, help="Metric before")
    p.add_argument("after", type=float, help="Metric after")
    p.add_argument("status", choices=["advance", "discard"], help="Result")
    p.add_argument("description", nargs="?", default="", help="Description")

    # skill
    p = sub.add_parser("skill", help="Manage shared skills")
    p.add_argument("action", choices=["add", "list", "get"])
    p.add_argument("name", nargs="?", help="Skill name")
    p.add_argument("--description", help="Skill description")
    p.add_argument("--by", default="unknown", help="Created by")

    # handoff
    p = sub.add_parser("handoff", help="Create agent handoff")
    p.add_argument("to", help="Target agent")
    p.add_argument("task", help="Task description")

    # status
    sub.add_parser("status", help="Show current state")

    # context
    sub.add_parser("context", help="Print context for LLM agents")

    # hit / miss
    sub.add_parser("hit", help="Mark target as achieved")
    p = sub.add_parser("miss", help="Mark target as missed")
    p.add_argument("reason", help="Why it was missed")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Load existing brain or create new
    if args.command == "init":
        brain = Brain(args.project)
    else:
        from pathlib import Path
        brain_path = Path.cwd() / ".shareclaw" / "brain.json"
        if brain_path.exists():
            import json
            with open(brain_path) as f:
                state = json.load(f)
            brain = Brain(state.get("project", "default"))
        else:
            print("⚠️  No ShareClaw brain found. Run: shareclaw init <project-name>")
            return
        

    if args.command == "init":
        brain._save()
        print(f"🧠 ShareClaw initialized: {args.project}")
        print(f"   State: {brain.brain_file}")
        print(f"   Run 'shareclaw target <your-goal>' to set your first target")

    elif args.command == "target":
        brain.set_target(args.target, args.deadline)

    elif args.command == "learn":
        brain.learn(args.what, args.evidence)

    elif args.command == "fail":
        brain.fail(args.what, args.reason)

    elif args.command == "cycle":
        brain.log_cycle(args.variable, args.variant, args.before,
                        args.after, args.status, args.description)

    elif args.command == "skill":
        if args.action == "add":
            brain.add_skill(args.name, args.description or "", created_by=args.by)
        elif args.action == "list":
            for s in brain.list_skills():
                print(f"  {s['name']} (v{s['version']}, {s['uses']} uses) — {s['description']}")
        elif args.action == "get":
            s = brain.get_skill(args.name)
            if s:
                print(f"  {s['name']} v{s['version']} by {s['created_by']}")
                print(f"  {s['description']}")
                if s.get("formula"):
                    print(f"  Formula: {s['formula']}")

    elif args.command == "handoff":
        brain.handoff(args.to, args.task)

    elif args.command == "status":
        brain.report()

    elif args.command == "context":
        print(brain.context())

    elif args.command == "hit":
        brain.hit_target()

    elif args.command == "miss":
        brain.miss_target(args.reason)


if __name__ == "__main__":
    main()
