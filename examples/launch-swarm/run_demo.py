#!/usr/bin/env python3
"""Run a deterministic launch-swarm demo using ShareClaw."""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shareclaw import Brain


DEMO_CYCLES = [
    {
        "target": "12 activated users/day",
        "variable": "launch_hook",
        "variant": "self-improving systems",
        "before": 4,
        "after": 13,
        "status": "advance",
        "description": "Ambitious framing made the launch instantly more legible",
        "learning": "Lead with self-improving systems, then explain the files and loops",
        "evidence": "Activated users/day moved from 4 to 13",
        "expected": "The broader systems framing would outperform plain 'agent memory'",
        "actual": "Visitors understood the ambition faster and more of them activated",
        "why": "The framing is both big and concrete: system, not gimmick",
        "next_action": "Keep the hook and test the CTA",
        "next_target": "18 activated users/day",
        "target_result": "hit",
        "event": "TARGET_HIT",
    },
    {
        "target": "18 activated users/day",
        "variable": "cta",
        "variant": "run the swarm",
        "before": 13,
        "after": 18,
        "status": "advance",
        "description": "CTA tied the concept to an action people could imagine immediately",
        "learning": "A CTA should invite people to try the swarm, not just star the repo",
        "evidence": "Activated users/day moved from 13 to 18",
        "expected": "A more active CTA would increase demo starts",
        "actual": "People clicked because the CTA promised a real experience",
        "why": "The action matched the story: this is a system you run, not just read about",
        "next_action": "Keep the CTA and test the demo angle",
        "next_target": "24 activated users/day",
        "target_result": "hit",
        "event": "TARGET_HIT",
    },
    {
        "target": "24 activated users/day",
        "variable": "demo_angle",
        "variant": "long architecture tour",
        "before": 18,
        "after": 15,
        "status": "discard",
        "description": "The architecture-heavy demo made the launch feel slower and less urgent",
        "failure": "Long architecture tours bury the payoff",
        "reason": "Activated users/day dropped from 18 to 15",
        "expected": "Deep technical walkthrough would build trust",
        "actual": "People bounced before they saw why the system mattered",
        "why": "Too much explanation before the first emotional payoff",
        "next_action": "Revert and ship a tighter terminal-first demo",
        "next_target": "28 activated users/day",
        "target_result": "missed",
        "event": "TARGET_MISSED",
    },
    {
        "target": "28 activated users/day",
        "variable": "demo_angle",
        "variant": "terminal swarm walkthrough",
        "before": 18,
        "after": 31,
        "status": "advance",
        "description": "A terminal-first demo made the system feel real, fast, and alive",
        "learning": "Show the swarm moving in the terminal before explaining the internals",
        "evidence": "Activated users/day moved from 18 to 31",
        "expected": "A concrete, high-signal demo would convert better than theory",
        "actual": "People immediately understood how the system coordinates and improves",
        "why": "The demo showed proof, not just promise",
        "next_action": "Package the benchmark and launch publicly",
        "next_target": "35 activated users/day",
        "target_result": "hit",
        "event": "TARGET_HIT",
    },
]


def run_demo(output_dir: Path, fresh: bool = False) -> dict:
    if fresh and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    brain = Brain(
        "launch-swarm-demo",
        path=str(output_dir / ".shareclaw"),
        objective="Grow activated users during the ShareClaw public launch",
        metric="activated_users_per_day",
        variables=["launch_hook", "cta", "demo_angle", "proof"],
        wait_time="1 day",
        step_size=1.4,
    )

    brain.emit(
        "LAUNCH_SWARM_STARTED",
        {"workspace": str(output_dir)},
        agent="orchestrator",
        details="Starting the ShareClaw launch-swarm demo",
    )

    decision_id = brain.start_consensus(
        "Should the launch center on 'self-improving systems'?",
        options=["SELF_IMPROVING_SYSTEMS", "MULTI_AGENT_MEMORY"],
        created_by="strategist",
        context="We need one sharp frame for the repo opening, launch post, and demo.",
    )
    brain.vote(
        decision_id,
        agent="research",
        choice="SELF_IMPROVING_SYSTEMS",
        reason="It captures the bigger promise while staying grounded in real workflow improvements.",
        data="User interviews react more strongly to system-level language than tooling language.",
        confidence=0.81,
    )
    brain.vote(
        decision_id,
        agent="builder",
        choice="SELF_IMPROVING_SYSTEMS",
        reason="The demo shows a system that coordinates and learns, not just memory storage.",
        data="Terminal walkthrough is strongest when paired with systems framing.",
        confidence=0.76,
    )
    brain.vote(
        decision_id,
        agent="analytics",
        choice="MULTI_AGENT_MEMORY",
        reason="It is narrower but more concrete, which can sometimes help click-through.",
        data="Past launches often rewarded simpler language.",
        confidence=0.62,
    )
    brain.resolve_consensus(decision_id, resolved_by="strategist")

    task_ids = {
        "demo": brain.create_task(
            "Ship terminal-first launch demo",
            priority="HIGH",
            details="Show tasks, consensus, events, and learning in one crisp run.",
            created_by="strategist",
        ),
        "readme": brain.create_task(
            "Rewrite README opening for public launch",
            priority="HIGH",
            details="Lead with the system promise and make the quick start obvious.",
            created_by="strategist",
        ),
        "thread": brain.create_task(
            "Draft launch thread and benchmark summary",
            priority="MED",
            details="Turn the benchmark result into a shareable story.",
            created_by="strategist",
        ),
    }

    picked_demo = brain.pickup_task("builder", task_ids["demo"])
    brain.complete_task(
        picked_demo["id"],
        "Terminal-first walkthrough scripted and ready for the launch page.",
        completed_by="builder",
    )
    brain.emit(
        "DEMO_READY",
        {"task_id": picked_demo["id"]},
        agent="builder",
        details="Terminal-first launch demo is ready.",
    )

    handoff_id = brain.handoff(
        "analytics",
        "Review the new terminal-first demo and log the result",
        context="Use the demo as the proof point for the launch.",
        files=["assets/demo_terminal.png", "README.md"],
        from_agent="builder",
    )
    brain.pickup_handoff("analytics")
    brain.complete_handoff(
        handoff_id,
        "Reviewed the demo, captured the conversion impact, and pushed the insight back into the brain.",
    )

    picked_readme = brain.pickup_task("content", task_ids["readme"])
    brain.complete_task(
        picked_readme["id"],
        "README opening now leads with the self-improving systems story.",
        completed_by="content",
    )

    brain.add_skill(
        "launch-opening-hook",
        description="Lead with the self-improving systems promise, then prove it with shared files and disciplined loops.",
        formula="big promise + concrete runtime + proof of improvement",
        examples_good=[
            "Build self-improving agent systems, not just isolated agents.",
            "Give your swarm a shared brain, task queue, and decision layer.",
        ],
        examples_bad=[
            "A JSON file for agents",
            "Another orchestration helper",
        ],
        code="shareclaw init launch-swarm --objective \"Grow activated users\" --metric activated_users",
        created_by="content",
    )

    for cycle in DEMO_CYCLES:
        brain.set_target(cycle["target"])
        brain.log_cycle(
            cycle["variable"],
            cycle["variant"],
            cycle["before"],
            cycle["after"],
            cycle["status"],
            cycle["description"],
        )
        if cycle["status"] == "advance":
            brain.learn(cycle["learning"], evidence=cycle["evidence"])
        else:
            brain.fail(cycle["failure"], reason=cycle["reason"])
        brain.introspect(
            expected=cycle["expected"],
            actual=cycle["actual"],
            why=cycle["why"],
            next_action=cycle["next_action"],
            next_target=cycle["next_target"],
        )
        brain.emit(
            "ANALYTICS_READY",
            {
                "variable": cycle["variable"],
                "variant": cycle["variant"],
                "after": cycle["after"],
            },
            agent="analytics",
            details=f"Measured cycle outcome for {cycle['variable']}={cycle['variant']}.",
        )
        if cycle["target_result"] == "hit":
            brain.hit_target()
        else:
            brain.miss_target(f"{cycle['variant']} underperformed versus the required launch target.")

    picked_thread = brain.pickup_task("content", task_ids["thread"])
    brain.complete_task(
        picked_thread["id"],
        "Launch thread drafted with benchmark proof, demo link, and clear CTA.",
        completed_by="content",
    )
    brain.emit(
        "LAUNCH_PACKAGE_READY",
        {"tasks_completed": 3},
        agent="orchestrator",
        details="Demo, README, and launch thread are ready.",
    )

    summary = {
        "project": brain.project,
        "objective": brain.objective,
        "metric": brain.metric,
        "winning_combo": brain.winning_combo(),
        "files": brain.files(),
        "open_tasks": len(brain.list_tasks(status="pending")),
        "completed_tasks": len(brain.list_tasks(status="completed")),
        "resolved_decisions": len(brain.list_decisions(status="resolved")),
        "recent_events": [event["type"] for event in brain.get_events(limit=8)],
    }
    summary_path = output_dir / "launch_swarm_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    brain.emit(
        "SUMMARY_WRITTEN",
        {"summary_path": str(summary_path)},
        agent="orchestrator",
        details="Wrote demo summary JSON.",
    )

    report = brain.report()
    print("Launch swarm demo complete.")
    print(f"Output directory: {output_dir}")
    print(f"Summary: {summary_path}")
    print("Key files:")
    for name, path in brain.files().items():
        print(f"  - {name}: {path}")
    print("\nFinal report:")
    print(report)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run the ShareClaw launch-swarm demo.")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / ".demo-output"),
        help="Where the demo workspace should be written.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete the existing output directory before running the demo.",
    )
    args = parser.parse_args()
    run_demo(Path(args.output_dir), fresh=args.fresh)


if __name__ == "__main__":
    main()
