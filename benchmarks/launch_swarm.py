#!/usr/bin/env python3
"""Benchmark a ShareClaw-style launch swarm against an ad-hoc swarm."""

from __future__ import annotations

import argparse
import json
import random
from collections import OrderedDict
from statistics import mean


VARIABLES = OrderedDict(
    [
        ("hook", ["agent memory", "shared brain", "multi-agent coordination", "self-improving systems"]),
        ("cta", ["star repo", "clone it", "run the swarm"]),
        ("demo", ["architecture tour", "code walkthrough", "terminal swarm walkthrough"]),
        ("proof", ["feature list", "demo snapshot", "benchmark graph"]),
    ]
)

BASE_CONFIG = {
    "hook": "agent memory",
    "cta": "star repo",
    "demo": "architecture tour",
    "proof": "feature list",
}

EFFECTS = {
    "hook": {
        "agent memory": 0,
        "shared brain": 5,
        "multi-agent coordination": 8,
        "self-improving systems": 15,
    },
    "cta": {
        "star repo": 0,
        "clone it": 4,
        "run the swarm": 9,
    },
    "demo": {
        "architecture tour": -2,
        "code walkthrough": 4,
        "terminal swarm walkthrough": 10,
    },
    "proof": {
        "feature list": 0,
        "demo snapshot": 3,
        "benchmark graph": 8,
    },
}


def score_config(config, rng):
    score = 18
    for variable, choice in config.items():
        score += EFFECTS[variable][choice]

    if config["hook"] == "self-improving systems" and config["demo"] == "terminal swarm walkthrough":
        score += 6
    if config["cta"] == "run the swarm" and config["proof"] == "benchmark graph":
        score += 4
    if config["hook"] == "shared brain" and config["proof"] == "demo snapshot":
        score += 2

    score += rng.gauss(0, 1.6)
    return round(max(score, 0), 2)


class AdHocSwarm:
    """A swarm that changes things, but doesn't keep durable memory of failures."""

    def __init__(self):
        self.config = dict(BASE_CONFIG)
        self.current_score = None

    def start(self, rng):
        self.current_score = score_config(self.config, rng)
        return self.current_score

    def step(self, rng):
        variable = rng.choice(list(VARIABLES.keys()))
        current = self.config[variable]
        choices = [choice for choice in VARIABLES[variable] if choice != current]
        candidate_choice = rng.choice(choices)
        candidate = dict(self.config)
        candidate[variable] = candidate_choice
        candidate_score = score_config(candidate, rng)

        # Ad-hoc teams keep changes when they look better, but they do not remember failed
        # variants and often revisit them later.
        if candidate_score >= self.current_score:
            self.config = candidate
            self.current_score = candidate_score
        return self.current_score


class ShareClawSwarm:
    """A swarm that explores methodically, keeps winners, and never repeats failed tests."""

    def __init__(self):
        self.config = dict(BASE_CONFIG)
        self.current_score = None
        self.variable_order = list(VARIABLES.keys())
        self.variable_index = 0
        self.failed_variants = {variable: set() for variable in VARIABLES}
        self.tested_variants = {variable: {BASE_CONFIG[variable]} for variable in VARIABLES}

    def start(self, rng):
        self.current_score = score_config(self.config, rng)
        return self.current_score

    def _next_candidate(self):
        checked = 0
        while checked < len(self.variable_order):
            variable = self.variable_order[self.variable_index]
            for choice in VARIABLES[variable]:
                if choice in self.tested_variants[variable]:
                    continue
                return variable, choice
            self.variable_index = (self.variable_index + 1) % len(self.variable_order)
            checked += 1
        return None, None

    def step(self, rng):
        variable, candidate_choice = self._next_candidate()
        if variable is None:
            return self.current_score

        candidate = dict(self.config)
        candidate[variable] = candidate_choice
        candidate_score = score_config(candidate, rng)
        self.tested_variants[variable].add(candidate_choice)

        if candidate_score >= self.current_score:
            self.config = candidate
            self.current_score = candidate_score
        else:
            self.failed_variants[variable].add(candidate_choice)

        # Move to the next variable only when we've tested the current one completely.
        variable_choices = set(VARIABLES[variable])
        if self.tested_variants[variable] >= variable_choices:
            self.variable_index = (self.variable_index + 1) % len(self.variable_order)

        return self.current_score


def run_trial(strategy_cls, cycles, seed):
    rng = random.Random(seed)
    strategy = strategy_cls()
    history = [strategy.start(rng)]
    for _ in range(cycles):
        history.append(strategy.step(rng))
    return history


def benchmark(trials, cycles, seed):
    ad_hoc_runs = []
    shareclaw_runs = []
    for offset in range(trials):
        ad_hoc_runs.append(run_trial(AdHocSwarm, cycles, seed + offset))
        shareclaw_runs.append(run_trial(ShareClawSwarm, cycles, seed + 10000 + offset))

    ad_hoc_by_cycle = [round(mean(run[idx] for run in ad_hoc_runs), 2) for idx in range(cycles + 1)]
    shareclaw_by_cycle = [
        round(mean(run[idx] for run in shareclaw_runs), 2) for idx in range(cycles + 1)
    ]

    threshold = 50
    ad_hoc_threshold = round(
        100 * sum(1 for run in ad_hoc_runs if run[-1] >= threshold) / trials,
        1,
    )
    shareclaw_threshold = round(
        100 * sum(1 for run in shareclaw_runs if run[-1] >= threshold) / trials,
        1,
    )

    ad_hoc_final = ad_hoc_by_cycle[-1]
    shareclaw_final = shareclaw_by_cycle[-1]
    summary = {
        "trials": trials,
        "cycles": cycles,
        "seed": seed,
        "baseline_strategy": "ad_hoc_swarm",
        "shareclaw_strategy": "shareclaw_swarm",
        "ad_hoc_average_by_cycle": ad_hoc_by_cycle,
        "shareclaw_average_by_cycle": shareclaw_by_cycle,
        "ad_hoc_final_average": ad_hoc_final,
        "shareclaw_final_average": shareclaw_final,
        "absolute_advantage": round(shareclaw_final - ad_hoc_final, 2),
        "relative_advantage_pct": round(((shareclaw_final / ad_hoc_final) - 1) * 100, 1),
        "threshold": threshold,
        "ad_hoc_threshold_hit_rate_pct": ad_hoc_threshold,
        "shareclaw_threshold_hit_rate_pct": shareclaw_threshold,
    }
    return summary


def format_report(summary):
    lines = [
        "ShareClaw Launch Benchmark",
        "",
        f"Trials: {summary['trials']}",
        f"Cycles per trial: {summary['cycles']}",
        f"Seed: {summary['seed']}",
        "",
        "Average activated users/day by cycle:",
        "",
        "Cycle | Ad-hoc swarm | ShareClaw swarm",
        "------|--------------|----------------",
    ]

    for idx, (ad_hoc, shareclaw) in enumerate(
        zip(summary["ad_hoc_average_by_cycle"], summary["shareclaw_average_by_cycle"])
    ):
        lines.append(f"{idx:>5} | {ad_hoc:>12} | {shareclaw:>14}")

    lines.extend(
        [
            "",
            f"Final average, ad-hoc swarm: {summary['ad_hoc_final_average']}",
            f"Final average, ShareClaw swarm: {summary['shareclaw_final_average']}",
            f"Absolute advantage: +{summary['absolute_advantage']}",
            f"Relative advantage: +{summary['relative_advantage_pct']}%",
            "",
            f"Threshold: {summary['threshold']} activated users/day",
            f"Ad-hoc hit rate: {summary['ad_hoc_threshold_hit_rate_pct']}%",
            f"ShareClaw hit rate: {summary['shareclaw_threshold_hit_rate_pct']}%",
        ]
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Benchmark a ShareClaw-style swarm.")
    parser.add_argument("--trials", type=int, default=200, help="Number of simulated launches")
    parser.add_argument("--cycles", type=int, default=12, help="Cycles per launch")
    parser.add_argument("--seed", type=int, default=7, help="Base RNG seed")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    summary = benchmark(args.trials, args.cycles, args.seed)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(format_report(summary))


if __name__ == "__main__":
    main()
